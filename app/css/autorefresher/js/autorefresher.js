(function ($) {
    //  The <div> element used when calling autoRefresher()
    let wrapper = null;

    //  The start button control
    let startButton = null;

    //  The stop button control
    let stopButton = null;

    //  The <div> element that is appended to the wrapper that acts as a 
    //  container for the progress bar
    let container = null;

    //  The <span> element that is appended to the container
    let pBar = null;

    //  The window.setTimeout function call
    let timeout = null;

    //  Is the timer in progress
    let inProgress = false;

    $.fn.autoRefresher = function (opts) {
        //  Create the options object by using the defaults as a template
        //  and overriding any properties that are provided in the opts given
        //  by the caller.
        let options = $.extend({}, $.fn.autoRefresher.defaults, opts);

        //  Ensure the seconds provided is a positive integer.  If it is not, then log that
        //  it is not and fallback to the default value
        if (!Number.isInteger(options.seconds) || options.seconds <= 0) {
            console.log('autoRefresher.options.seconds must be a positive integer. Switching to default value');
            options.seconds = $.fn.autoRefresher.defaults.seconds;
        }

        //  Ensure that the callback function provided is actually a function.  If it is not,
        //  then log that it is not and fallback to the default
        if (!$.isFunction(options.callback)) {
            console.log('autoRefresher.options.callback must be a function.  Switching to default function');
            options.callback = $.fn.autoRefresher.defaults.callback;
        }

        //  Ensure that the value provided for the startButtonClass isn't null or just an empty string.
        //  If it is null or empty string, then log that and fallback to the default value.
        if(options.startButtonClass === null || options.startButtonClass.trim().length === 0) {
            options.startButtonClass = $.fn.autoRefresher.defaults.startButtonClass;
        }

        //  Ensure that the value provided for the stopButtonClass isn't null or just an empty string.
        //  if it is null or empty string, then log that and fallback to the default value.
        if(options.stopButtonClass === null || options.stopButtonClass.trim().length === 0) {
            options.stopButtonClass = $.fn.autoRefresher.defaults.stopButtonClass;
        }        

        

        //  The element that was used to call the autoRefresher() method is the wrapper
        //  that is used for the entire thing
        wrapper = $(this);

        //  Creates a trigger that users can call to start everything using
        //  their own controls instead of having to use the controls provided
        //  by this plugin.
        wrapper.on('stop', function() {
            stop();
        });

        //  Create a trigger that users can call to stop everything using
        //  their own controls instead of having to use the controls provided
        //  by this plugin.
        wrapper.on('start', function() {
            start();
        })

        //  Add the needed css class for the wrapper'
        if(!wrapper.hasClass('auto-refresher')) {
            wrapper.addClass('auto-refresher');
        }

        //  If the caller opted to have the controls included, add them now by 
        //  appending them to the wrapper
        if (options.showControls) {
            stopButton = $('<button />')
                            .attr({type: 'button', class: options.stopButtonClass})
                            .html(options.stopButtonInner)
                            .appendTo(wrapper);
            stopButton.on('click', function() {
                stop();
            });

            startButton = $('<button />')
                            .attr({type: 'button', class: options.startButtonClass})
                            .html(options.startButtonInner)
                            .appendTo(wrapper);
            startButton.on('click', function() {
                start();
            });
        }

        //  Create and append the progress bar container <div> element
        if(container === null) {
            container = $('<div />')
                            .attr({'class': 'auto-refresher-container'})
                            .css({'height': options.progressBarHeight})
                            .css({'background-color': options.backgroundColor})
                            .appendTo(wrapper);
        }

        //  Create an append the progress bar <span> element
        if(pBar === null) {
            pBar = $('<span />')
                        .attr({'class': 'auto-refresher-progress-bar'})
                        .css({'background-color': options.foregroundColor})
                        .appendTo(container);
        }

        start();

        /**
         * Kicks off the auto refresh process. Creates a timeout that
         * will execute the options.callback method after the period of
         * time defined by options.seconds.
         */
        function start() {
            //  Don't continue if we are already in progress
            if(inProgress) {return;}
            inProgress = true;

            //  set the transition property to the number of seconds to
            //  wait for auto refreshing
            pBar.css({'transition': options.seconds + 's linear'});

            //  Set the width of the progress bar to 100.  This in combination
            //  with setting the transition time above creates a faux animation
            //  of the progress bar filling up for that amount of time
            pBar.width('100%');

            //  Create the timeout that will execute the callback function
            //  when it's completed.
            timeout =  window.setTimeout(function () {
                pBar.css({'transition': ''});
                if ($.isFunction(options.callback)) {
                    options.callback();
                }
            }, options.seconds * 1000);
        }
        
        /**
         * Stops the auto refresh process completely.  Clears the timeout
         * that was created during start().
         */
        function stop() {
            //  Don't continue if we are not in progress
            if(!inProgress) {return;}
            inProgress = false;

            //  Disable the transition property on the progress bar
            pBar.css({'transition': ''});

            //  set the width of the progress bar to 0 to visually show
            //  that we have stopped
            pBar.width('0%');

            //  Clear the timeout that was created when we started.
            window.clearTimeout(timeout);
        }
    }

    $.fn.autoRefresher.defaults = {
        seconds: 300,
        callback: function () {
            location.reload();
        },
        showControls: true,
        progressBarHeight: '7px',
        stopButtonClass: 'auto-refresher-button',
        stopButtonInner: 'Stop',
        startButtonClass: 'auto-refresher-button',
        startButtonInner: 'Start',
        backgroundColor: '#6c757d',
        foregroundColor: '#007bff'
    }

})(jQuery);