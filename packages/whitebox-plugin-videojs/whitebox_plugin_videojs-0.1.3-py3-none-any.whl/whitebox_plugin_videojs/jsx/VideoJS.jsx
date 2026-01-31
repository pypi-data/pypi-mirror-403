// This file was initially created from an example in the Videojs.com documentation:
// https://github.com/videojs/videojs.com/blob/6a9dbb6cf044c371423ebc6ac432777a6ff515ec/src/mdx-pages/guides/react.mdx
// Some local changes apply. For more info, refer to comments & Whitebox Git history.

// Considering that this is not currently testable (actual videojs player code
// is sourced from backend, which is not available during the test runtime), we
// will not be adding tests for this component for now.
/* v8 ignore start */


// The example was written by multiple authors, which you can find in the
// Videojs.com's source's git history, available on the above URL.

// The example source code is licensed under the MIT License, which is copied
// below, and also available here: https://github.com/videojs/videojs.com/blob/6a9dbb6cf044c371423ebc6ac432777a6ff515ec/LICENSE

/*
The MIT License (MIT)

Copyright (c) Brightcove, Inc

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
 */

import {useEffect, useRef} from "react";

const VideoJS = (props) => {
  const videoRef = useRef(null)
  const playerRef = useRef(null)
  const {options, onReady} = props

  useEffect(() => {
    // Make sure Video.js player is only initialized once
    if (!playerRef.current) {
      // The Video.js player needs to be _inside_ the component el for React 18 Strict Mode.
      const videoElement = document.createElement("video-js")

      videoElement.classList.add('vjs-big-play-centered')
      videoRef.current.appendChild(videoElement)

      const player = playerRef.current = window.videojs(videoElement, options, () => {
        onReady && onReady(player)
      })

    // You could update an existing player in the `else` block here
    // on prop change, for example:
    } else {
      const player = playerRef.current

      player.autoplay(options.autoplay)
      player.src(options.sources)
    }
  }, [options, onReady, videoRef])

  // Dispose the Video.js player when the functional component unmounts
  useEffect(() => {
    const player = playerRef.current

    return () => {
      if (player && !player.isDisposed()) {
        player.dispose()
        playerRef.current = null
      }
    }
  }, [playerRef])

  return (
    <div data-vjs-player className="w-full h-full">
      <div ref={videoRef} />
    </div>
  )
}

export {
  VideoJS,
}
export default VideoJS
