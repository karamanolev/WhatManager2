function DGPlayer(root, playActive, pause, pauseActive) {
    function volumeTrans(value) {
        return Math.pow(value / 100, 2) * 100;
    }

    function volumeUntrans(value) {
        return Math.pow(value / 100, 1 / 2) * 100;
    }

    // Get elements
    var events = {},
        state = 'paused';

    // Preload images
    new Image().src = playActive;
    new Image().src = pause;
    new Image().src = pauseActive;
//    new Image().src = "/dgplayer/resources/choosefile_pressed.png";

    // Prevent text selection in IE
    root.onselectstart = function () {
        return false
    }

    var seekBar = (function () {

        var loading = root.querySelector(".seek .track .loaded"),
            progress = root.querySelector(".seek .track .progress"),
            played = root.querySelector(".seek span:first-child"),
            remaining = root.querySelector(".seek span:last-child"),
            track = root.querySelector(".seek .track"),
            maxWidth = loading.parentNode.offsetWidth - 2,
            loaded = 0, currentTime = 0, trackLength = 0, oldSeconds = 0;


        track.addEventListener('mousedown', function (e) {
            var offsetX = e.offsetX || e.layerX;
            var part = Math.min(1, Math.max(0, offsetX / maxWidth));
            var milli = trackLength * part;
            emit('seek', milli);
        }, false);

        function pad(input) {
            return ("00" + input).slice(-2);
        }

        return {
            getTrackLength: function () {
                return trackLength;
            },

            setTrackLength: function (time) {
                trackLength = time;
                this.seekTime = currentTime;
            },

            getCurrentTime: function () {
                return currentTime;
            },

            setCurrentTime: function (time) {
                oldSeconds = Math.floor(currentTime / 1000 % 60);

                currentTime = time;

//                if (currentTime >= trackLength && trackLength > 0)
//                    emit("pause");

                var t = currentTime / 1000,
                    seconds = Math.floor(t % 60),
                    minutes = Math.floor((t /= 60) % 60);

                if (seconds === oldSeconds)
                    return;

                played.innerHTML = minutes + ':' + pad(seconds);

                // only show the progress bar and remaining time if we know the duration
                if (trackLength > 0) {
                    var r = (trackLength - currentTime) / 1000,
                        remainingSeconds = Math.floor(r % 60),
                        remainingMinutes = Math.floor((r /= 60) % 60);

                    remaining.innerHTML = '-' + remainingMinutes + ':' + pad(remainingSeconds);
                    position = Math.max(0, Math.min(1, currentTime / trackLength));
                    progress.style.width = maxWidth * position + 'px';
                } else {
                    remaining.innerHTML = '-0:00';
                }
            },

            getAmountLoaded: function () {
                return loaded;
            },

            setAmountLoaded: function (val) {
                loaded = Math.max(0, Math.min(100, val));
                loading.style.width = maxWidth * (loaded / 100) + 'px';
            }
        }

    })();

    var playpause = (function () {

        var button = root.querySelector(".button"),
            interval = null, playing = false;

        button.onclick = function () {
            emit(playing ? "pause" : "play");
        };

        root.addEventListener('keyup', function (e) {
            e.which === 32 && emit(playing ? "pause" : "play");
        });

        function setPlaying(play) {
            if (playing = play)
                button.classList.add("pause");
            else
                button.classList.remove("pause");
        }

        return {
            setPlaying: setPlaying,
            getPlaying: function () {
                return playing;
            }
        }

    })();

    var slider = (function () {

        var handle = root.querySelector(".volume .handle"),
            progress = root.querySelector(".volume .progress"),
            track = root.querySelector(".volume .track")
        volumeLeft = root.querySelector(".volume img:first-child"),
            volumeRight = root.querySelector(".volume img:last-child");

        var lastY = 0,
            down = false,
            height = 65,
            handleSize = 20,
            min = -8,
            max = height - handleSize / 2 - 3,
            curY = Math.floor(height / 2 - handleSize / 2),
            value = 50;

        function update(dontEmit) {
            if ('webkitTransform' in handle.style)
                handle.style.webkitTransform = "translate3d(0, " + (-max - min + curY) + "px" + ", 0)";
            else
                handle.style.bottom = max + min - curY + "px";

            progress.style.height = max - curY + "px";
            value = Math.round(100 - (curY - min) / (max - min) * 100);

            if (!dontEmit)
                emit("volume", volumeTrans(value));
        }

        update();

        handle.onmousedown = handle.ontouchstart = function (e) {
            lastY = e.targetTouches ? e.targetTouches[0].pageY : e.clientY;
            down = true;
            e.stopPropagation();
            handle.classList.add("active");
            e.preventDefault();
        }

        function onMove(e) {
            var eventY = e.targetTouches ? e.targetTouches[0].pageY : e.clientY;
            var y = Math.max(min, Math.min(max, curY + eventY - lastY));
            if (!down || y === curY) return;

            curY = y;
            lastY = eventY;
            update();
        }

        function onUp(e) {
            if (!down) return;
            down = false;
            handle.classList.remove("active");
        }

        document.addEventListener("mousemove", onMove, false);
        document.addEventListener("touchmove", onMove, false);
        document.addEventListener("mouseup", onUp, false);
        document.addEventListener("touchend", onUp, false);

        // Handle clicking on the minimum and maximum volume icons
        function animate() {
            handle.classList.add("animatable");
            progress.classList.add("animatable");

            update();

            setTimeout(function () {
                handle.classList.remove("animatable");
                progress.classList.remove("animatable");
            }, 250);
        }

        volumeLeft.onclick = function () {
            curY = min;
            animate();
        }

        volumeRight.onclick = function () {
            curY = max;
            animate();
        }

        // Handle clicking on the track
        track.onmousedown = track.ontouchstart = function (e) {
            var y = e.targetTouches ? e.targetTouches[0].pageY : e.clientY;

            // Get the absolute offsetTop of the track
            var offset = 0, obj = track;
            while (obj) {
                offset += obj.offsetTop - obj.scrollTop;
                obj = obj.offsetParent;
            }

            curY = Math.max(min, Math.min(max, y - offset - (handleSize + min)));
            handle.onmousedown(e);
            update();
        }

        return {
            getValue: function () {
                return volumeTrans(value);
            },

            setValue: function (val) {
                val = Math.max(0, Math.min(100, val));
                val = volumeUntrans(val);

                curY = max - (val / 100) * (max - min);
                update(true);
            }
        }

    })();

//    var filebutton = (function() {
//
//        var button = root.querySelector('.file_button'),
//            input = document.createElement('input');
//
//        input.setAttribute('type', 'file');
//        input.style.opacity = 0;
//        input.style.position = 'absolute';
//        input.style.left = '-1000px';
//
//        input.onchange = function(e) {
//            emit('file', input.files[0]);
//        }
//
//        button.onclick = function() {
//            input.click();
//        }
//
//    })();

    function emit(event) {
        if (!events[event]) return;

        var args = Array.prototype.slice.call(arguments, 1),
            callbacks = events[event];

        for (var i = 0, len = callbacks.length; i < len; i++) {
            callbacks[i].apply(null, args);
        }
    }

    var API = {
        on: function (event, fn) {
            events[event] || (events[event] = []);
            events[event].push(fn);
        },

        off: function (event, fn) {
            var eventsOf = events[event],
                index = eventsOf.indexOf(fn);

            ~index && eventsOf.splice(index, 1);
        }
    };

    // Object.defineProperty shim for Opera
    Object.defineProperty || (Object.defineProperty = function (obj, prop, config) {
        if (config.get && obj.__defineGetter__)
            obj.__defineGetter__(prop, config.get);

        if (config.set && obj.__defineSetter__)
            obj.__defineSetter__(prop, config.set);
    })

    Object.defineProperty(API, "bufferProgress", {
        get: seekBar.getAmountLoaded,
        set: seekBar.setAmountLoaded
    });

    Object.defineProperty(API, "state", {
        set: function (newstate) {
            playpause.setPlaying(newstate == 'playing' || newstate == 'buffering');
            state = newstate;
        },

        get: function () {
            return state;
        }
    });

    Object.defineProperty(API, "duration", {
        get: seekBar.getTrackLength,
        set: seekBar.setTrackLength
    });

    Object.defineProperty(API, "seekTime", {
        get: seekBar.getCurrentTime,
        set: seekBar.setCurrentTime
    });

    Object.defineProperty(API, "volume", {
        get: slider.getValue,
        set: slider.setValue
    });

    var img = root.querySelector(".avatar img");
    Object.defineProperty(API, "coverArt", {
        get: function () {
            return img.src;
        },

        set: function (src) {
            img.src = src;
        }
    });

    var title = root.querySelector("span.title"),
        artist = root.querySelector("span.artist");

    Object.defineProperty(API, "songTitle", {
        get: function () {
            return title.innerHTML;
        },

        set: function (val) {
            title.innerHTML = val;
        }
    });

    Object.defineProperty(API, "songArtist", {
        get: function () {
            return artist.innerHTML;
        },

        set: function (val) {
            artist.innerHTML = val;
        }
    });

//    var description = root.querySelector('.file_description');
//    Object.defineProperty(API, "fileDescription", {
//        get: function() {
//            return description.innerHTML;
//        },
//
//        set: function(val) {
//            description.innerHTML = val;
//        }
//    });

    return API;

}