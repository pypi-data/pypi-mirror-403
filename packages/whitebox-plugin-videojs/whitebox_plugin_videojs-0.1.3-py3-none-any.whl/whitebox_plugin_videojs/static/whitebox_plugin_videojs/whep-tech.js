/**
 * WHEP Tech for Video.js
 *
 * Implements WebRTC-HTTP Egress Protocol (WHEP) for Video.js
 * Provides low-latency live streaming via WebRTC with automatic reconnection.
 *
 * Usage:
 *   player.src({
 *     src: 'http://srs-host:1985/rtc/v1/whep/?app=live&stream=livestream',
 *     type: 'application/whep'
 *   });
 *
 * Events:
 *   - whep:connecting    : Starting WHEP negotiation
 *   - whep:connected     : WebRTC connection established
 *   - whep:streaming     : First frame received, stream is playing
 *   - whep:disconnected  : Connection lost
 *   - whep:reconnecting  : Attempting to reconnect
 *   - whep:error         : Error occurred (check event.detail)
 *
 * @license AGPL-3.0
 */
(function (window, videojs) {
  "use strict";

  if (!videojs) {
    console.error("[WhepTech] Video.js not found");
    return;
  }

  const Tech = videojs.getTech("Tech");

  if (!Tech) {
    console.error("[WhepTech] Video.js Tech base not found");
    return;
  }

  // Connection states
  const STATE = {
    IDLE: "idle",
    CONNECTING: "connecting",
    CONNECTED: "connected",
    STREAMING: "streaming",
    DISCONNECTED: "disconnected",
    RECONNECTING: "reconnecting",
    FAILED: "failed",
    CLOSED: "closed",
  };

  // Default configuration
  const DEFAULT_RETRY_DELAYS = [1000, 2000, 4000, 8000, 16000];
  const DEFAULT_MAX_RETRIES = 5;
  const DEFAULT_ICE_TIMEOUT = 10000; // 10 seconds

  /**
   * Wait for ICE gathering to complete with timeout
   * @param {RTCPeerConnection} pc - The peer connection
   * @param {number} timeout - Timeout in milliseconds
   * @returns {Promise<void>}
   */
  function waitForIceComplete(pc, timeout = DEFAULT_ICE_TIMEOUT) {
    if (pc.iceGatheringState === "complete") {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      let resolved = false;

      const cleanup = () => {
        if (resolved) return;
        resolved = true;
        pc.removeEventListener("icegatheringstatechange", onStateChange);
        pc.removeEventListener("icecandidate", onCandidate);
      };

      const onStateChange = () => {
        if (pc.iceGatheringState === "complete") {
          cleanup();
          resolve();
        }
      };

      const onCandidate = (event) => {
        if (event.candidate === null) {
          cleanup();
          resolve();
        }
      };

      pc.addEventListener("icegatheringstatechange", onStateChange);
      pc.addEventListener("icecandidate", onCandidate);

      // Timeout to prevent hanging forever
      setTimeout(() => {
        if (!resolved) {
          cleanup();
          // Resolve anyway - we may have enough candidates
          resolve();
        }
      }, timeout);
    });
  }

  /**
   * Create TimeRanges object with Video.js compatibility
   * @param {Array} ranges - Array of [start, end] tuples
   * @returns {TimeRanges}
   */
  function createTimeRanges(ranges) {
    const fn =
      (videojs.time && videojs.time.createTimeRanges) ||
      videojs.createTimeRanges ||
      videojs.createTimeRange;

    if (fn) {
      return fn(ranges);
    }

    // Fallback implementation
    return {
      length: ranges.length,
      start: (i) => ranges[i][0],
      end: (i) => ranges[i][1],
    };
  }

  /**
   * WhepTech - Video.js Tech for WHEP protocol
   * Extends Tech base class for WebRTC streaming
   */
  class WhepTech extends Tech {
    constructor(options, ready) {
      super(options, ready);

      // WebRTC state
      this.pc_ = null;
      this.mediaStream_ = null;
      this.abortController_ = null;

      // WHEP configuration
      this.whepUrl_ = "";
      this.connectionState_ = STATE.IDLE;

      // Retry configuration
      this.retryCount_ = 0;
      this.retryDelays_ = options.whep?.retryDelays || DEFAULT_RETRY_DELAYS;
      this.maxRetries_ = options.whep?.maxRetries || DEFAULT_MAX_RETRIES;
      this.retryTimeout_ = null;

      // Playback state
      this.paused_ = !options.autoplay;
      this.hasReceivedFrame_ = false;

      // Event handler references for cleanup
      this.boundEventHandlers_ = null;

      // Handle source from options (Video.js passes it here for custom techs)
      if (options.source?.src) {
        this.whepUrl_ = options.source.src;
      }

      // Signal ready
      this.triggerReady();

      // If autoplay is enabled and we have a source, start connection
      if (options.autoplay && this.whepUrl_) {
        this.startConnection_();
      }
    }

    /* ========================================================================
     * Element Management
     * ======================================================================== */

    createEl() {
      if (this.el_) {
        return this.el_;
      }

      // Create video element with appropriate attributes
      this.el_ = videojs.dom.createEl("video", {
        className: "vjs-tech",
      });

      // Set attributes for live streaming
      this.el_.setAttribute("playsinline", "");
      this.el_.muted = true;
      this.el_.autoplay = false;

      // Events to forward from native video element to Video.js
      const forwardedEvents = [
        "loadstart",
        "loadedmetadata",
        "loadeddata",
        "canplay",
        "canplaythrough",
        "play",
        "playing",
        "pause",
        "ended",
        "timeupdate",
        "progress",
        "waiting",
        "stalled",
        "error",
        "volumechange",
        "ratechange",
      ];

      // Store handlers for cleanup
      const forwardHandler = (e) => this.trigger(e.type);
      const onFirstFrame = () => {
        if (!this.hasReceivedFrame_) {
          this.hasReceivedFrame_ = true;
          this.updateConnectionState_(STATE.STREAMING);
          this.triggerWhepEvent_("streaming");
        }
      };

      this.boundEventHandlers_ = {
        forward: forwardHandler,
        firstFrame: onFirstFrame,
        forwardedEvents: forwardedEvents,
      };

      // Forward native video events to Video.js
      forwardedEvents.forEach((event) => {
        this.el_.addEventListener(event, forwardHandler);
      });

      // Track when we receive the first frame
      // Use multiple events for reliability across browsers with WebRTC MediaStream
      this.el_.addEventListener("loadeddata", onFirstFrame);
      this.el_.addEventListener("playing", onFirstFrame);
      this.el_.addEventListener("canplay", onFirstFrame);

      return this.el_;
    }

    dispose() {
      // Clear retry timeout
      if (this.retryTimeout_) {
        clearTimeout(this.retryTimeout_);
        this.retryTimeout_ = null;
      }

      // Stop WebRTC connection
      this.stopConnection_();

      // Remove event listeners from video element
      if (this.el_ && this.boundEventHandlers_) {
        const { forward, firstFrame, forwardedEvents } = this.boundEventHandlers_;
        forwardedEvents.forEach((event) => {
          this.el_.removeEventListener(event, forward);
        });
        this.el_.removeEventListener("loadeddata", firstFrame);
        this.el_.removeEventListener("playing", firstFrame);
        this.el_.removeEventListener("canplay", firstFrame);
        this.boundEventHandlers_ = null;
      }

      // Update state
      this.updateConnectionState_(STATE.CLOSED);

      // Call parent dispose
      super.dispose();
    }

    /* ========================================================================
     * Playback State
     * ======================================================================== */

    paused() {
      return this.el_ ? this.el_.paused : this.paused_;
    }

    seeking() {
      return false; // Live WHEP streams are not seekable
    }

    ended() {
      return false; // Live WHEP streams don't end
    }

    currentTime() {
      return this.el_ ? this.el_.currentTime : 0;
    }

    setCurrentTime() {
      // No-op: Live streams are not seekable
    }

    duration() {
      // Return Infinity for live streams
      return Infinity;
    }

    buffered() {
      return this.el_?.buffered || createTimeRanges([]);
    }

    played() {
      return this.el_?.played || createTimeRanges([]);
    }

    seekable() {
      return createTimeRanges([]); // Live streams are not seekable
    }

    readyState() {
      return this.el_?.readyState || 0;
    }

    networkState() {
      return this.el_?.networkState || 0;
    }

    /* ========================================================================
     * Video Element Properties
     * ======================================================================== */

    setProp_(name, value) {
      if (this.el_) {
        this.el_[name] = value;
      }
    }

    getProp_(name, fallback) {
      return this.el_ ? this.el_[name] : fallback;
    }

    setControls(val) {
      this.setProp_("controls", !!val);
    }
    controls() {
      return !!this.getProp_("controls", false);
    }

    setAutoplay(val) {
      this.setProp_("autoplay", !!val);
    }
    autoplay() {
      return !!this.getProp_("autoplay", false);
    }

    setLoop(val) {
      this.setProp_("loop", !!val);
    }
    loop() {
      return !!this.getProp_("loop", false);
    }

    setMuted(val) {
      this.setProp_("muted", !!val);
      this.trigger("volumechange");
    }
    muted() {
      return !!this.getProp_("muted", true);
    }

    setVolume(val) {
      this.setProp_("volume", Number(val));
      this.trigger("volumechange");
    }
    volume() {
      return this.getProp_("volume", 1);
    }

    setPlaysinline(val) {
      if (this.el_) {
        if (val) {
          this.el_.setAttribute("playsinline", "");
        } else {
          this.el_.removeAttribute("playsinline");
        }
      }
    }
    playsinline() {
      return !!(this.el_ && this.el_.hasAttribute("playsinline"));
    }

    setPreload(val) {
      this.setProp_("preload", val || "auto");
    }
    preload() {
      return this.getProp_("preload", "auto");
    }

    setPoster(url) {
      this.setProp_("poster", url || "");
    }
    poster() {
      return this.getProp_("poster", "");
    }

    playbackRate() {
      return this.getProp_("playbackRate", 1);
    }
    setPlaybackRate(rate) {
      const r = Number(rate);
      if (Number.isFinite(r) && r > 0) {
        this.setProp_("playbackRate", r);
        this.trigger("ratechange");
      }
    }

    defaultPlaybackRate() {
      return this.getProp_("defaultPlaybackRate", 1);
    }
    setDefaultPlaybackRate(rate) {
      const r = Number(rate);
      if (Number.isFinite(r) && r > 0) {
        this.setProp_("defaultPlaybackRate", r);
        this.trigger("ratechange");
      }
    }

    /* ========================================================================
     * Source Management
     * ======================================================================== */

    setSrc(src) {
      this.whepUrl_ = src || "";
      this.hasReceivedFrame_ = false;
      this.retryCount_ = 0;

      this.trigger("loadstart");
      this.triggerSourceset(this.whepUrl_);

      // If not paused (play was already called), start connection now
      if (!this.paused_ && this.whepUrl_ && !this.pc_) {
        this.startConnection_();
      }
    }

    src() {
      return this.whepUrl_;
    }

    /* ========================================================================
     * Playback Control
     * ======================================================================== */

    play() {
      this.paused_ = false;
      this.trigger("play");

      // Start WHEP connection if not already connected
      if (!this.pc_ && this.whepUrl_) {
        this.startConnection_();
      } else if (this.el_) {
        // Already connected, just play
        this.el_.play().catch(() => {});
      }

      return Promise.resolve();
    }

    pause() {
      this.paused_ = true;
      if (this.el_) {
        this.el_.pause();
      }
      this.trigger("pause");
    }

    /* ========================================================================
     * WHEP Protocol Implementation
     * ======================================================================== */

    async startConnection_() {
      if (this.connectionState_ === STATE.CONNECTING) {
        return;
      }

      this.updateConnectionState_(STATE.CONNECTING);
      this.triggerWhepEvent_("connecting");

      try {
        await this.negotiateWhep_();
        this.updateConnectionState_(STATE.CONNECTED);
        this.triggerWhepEvent_("connected");
      } catch (error) {
        console.error("[WhepTech] Connection failed:", error);
        this.handleConnectionError_(error);
      }
    }

    async negotiateWhep_() {
      // Create abort controller for this request
      this.abortController_ = new AbortController();

      // Get RTC configuration from options
      const rtcConfig = this.options_?.whep?.rtcConfig || {};

      // Create peer connection
      const pc = new RTCPeerConnection(rtcConfig);
      this.pc_ = pc;

      // Add transceivers for receiving audio and video
      pc.addTransceiver("video", { direction: "recvonly" });
      pc.addTransceiver("audio", { direction: "recvonly" });

      // Handle incoming tracks
      pc.ontrack = (event) => {
        if (!this.mediaStream_) {
          this.mediaStream_ = new MediaStream();
        }

        // Avoid duplicate tracks
        const existingTrack = this.mediaStream_
          .getTracks()
          .find((t) => t.id === event.track.id);
        if (!existingTrack) {
          this.mediaStream_.addTrack(event.track);
        }

        // Attach stream to video element
        if (this.el_) {
          this.el_.srcObject = this.mediaStream_;
          this.el_.play().catch(() => {});
        }
      };

      // Handle connection state changes
      pc.onconnectionstatechange = () => {
        switch (pc.connectionState) {
          case "connected":
            this.retryCount_ = 0; // Reset retry count on successful connection
            break;
          case "disconnected":
          case "failed":
            this.handleDisconnection_();
            break;
          case "closed":
            this.updateConnectionState_(STATE.CLOSED);
            break;
        }
      };

      // Handle ICE connection state
      pc.oniceconnectionstatechange = () => {
        if (
          pc.iceConnectionState === "failed" ||
          pc.iceConnectionState === "disconnected"
        ) {
          this.handleDisconnection_();
        }
      };

      // Create SDP offer
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      // Wait for ICE gathering to complete (with timeout)
      await waitForIceComplete(pc);

      // Send offer to WHEP endpoint
      const response = await fetch(this.whepUrl_, {
        method: "POST",
        headers: {
          "Content-Type": "application/sdp",
        },
        body: pc.localDescription.sdp,
        signal: this.abortController_.signal,
      });

      if (!response.ok) {
        const errorText = await response.text().catch(() => "");
        throw new Error(`WHEP request failed: ${response.status} ${errorText}`);
      }

      // Apply SDP answer
      const answerSdp = await response.text();
      await pc.setRemoteDescription({
        type: "answer",
        sdp: answerSdp,
      });
    }

    stopConnection_() {
      // Abort any pending fetch
      if (this.abortController_) {
        this.abortController_.abort();
        this.abortController_ = null;
      }

      // Clear srcObject
      if (this.el_) {
        this.el_.srcObject = null;
      }

      // Close peer connection
      if (this.pc_) {
        this.pc_.close();
        this.pc_ = null;
      }

      // Clear media stream
      if (this.mediaStream_) {
        this.mediaStream_.getTracks().forEach((track) => track.stop());
        this.mediaStream_ = null;
      }

      this.hasReceivedFrame_ = false;
    }

    /* ========================================================================
     * Error Handling and Reconnection
     * ======================================================================== */

    handleConnectionError_(error) {
      this.triggerWhepEvent_("error", { message: error.message });
      this.scheduleReconnect_();
    }

    handleDisconnection_() {
      if (
        this.connectionState_ === STATE.CLOSED ||
        this.connectionState_ === STATE.RECONNECTING
      ) {
        return;
      }

      this.updateConnectionState_(STATE.DISCONNECTED);
      this.triggerWhepEvent_("disconnected");
      this.stopConnection_();
      this.scheduleReconnect_();
    }

    scheduleReconnect_() {
      if (this.connectionState_ === STATE.CLOSED) {
        return;
      }

      if (this.retryCount_ >= this.maxRetries_) {
        this.updateConnectionState_(STATE.FAILED);
        this.triggerWhepEvent_("error", {
          message: "Max reconnection attempts reached",
          code: "MAX_RETRIES",
        });
        return;
      }

      const delay =
        this.retryDelays_[
          Math.min(this.retryCount_, this.retryDelays_.length - 1)
        ];
      this.retryCount_++;

      this.updateConnectionState_(STATE.RECONNECTING);
      this.triggerWhepEvent_("reconnecting", {
        attempt: this.retryCount_,
        maxAttempts: this.maxRetries_,
        delay: delay,
      });

      this.retryTimeout_ = setTimeout(() => {
        this.retryTimeout_ = null;
        if (
          this.connectionState_ !== STATE.CLOSED &&
          this.connectionState_ !== STATE.CONNECTED &&
          this.connectionState_ !== STATE.STREAMING
        ) {
          this.startConnection_();
        }
      }, delay);
    }

    /* ========================================================================
     * State Management
     * ======================================================================== */

    updateConnectionState_(state) {
      this.connectionState_ = state;
    }

    getConnectionState() {
      return this.connectionState_;
    }

    triggerWhepEvent_(eventName, detail = {}) {
      this.trigger(`whep:${eventName}`, detail);
    }

    /* ========================================================================
     * Static Methods
     * ======================================================================== */

    static isSupported() {
      return (
        typeof window.RTCPeerConnection === "function" &&
        typeof window.fetch === "function"
      );
    }

    static canPlayType(type) {
      return type === "application/whep" ? "probably" : "";
    }

    static canPlaySource(srcObj) {
      return srcObj?.type === "application/whep" ? "probably" : "";
    }
  }

  // Enable source handler pattern for Video.js
  Tech.withSourceHandlers(WhepTech);

  // Register source handler
  WhepTech.registerSourceHandler({
    canHandleSource(srcObj) {
      return srcObj?.type === "application/whep" ? "probably" : "";
    },
    canPlayType(type) {
      return type === "application/whep" ? "probably" : "";
    },
    handleSource(srcObj, tech) {
      tech.setSrc(srcObj.src);
      return {
        dispose() {
          tech.stopConnection_?.();
        },
      };
    },
  });

  // Register the tech with Video.js
  videojs.registerTech("WhepTech", WhepTech);

  // Export for module systems
  if (typeof module !== "undefined" && module.exports) {
    module.exports = WhepTech;
  }
})(window, window.videojs);
