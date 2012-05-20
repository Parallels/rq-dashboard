define(['jquery'], function($) {

    var getQueues = function(cb) {
        $.getJSON('/queues', function(data) { // TODO: Fix static URL
            var queues = data.queues;
            cb(queues);
        });
    };

    var getJobs = function(queue_name, cb) {
        $.getJSON('/jobs/' + encodeURIComponent(queue_name), function(data) { // TODO: Fix static URL
            var jobs = data.jobs;
            cb(jobs);
        });
    };

    var getWorkers = function(cb) {
        $.getJSON('/workers', function(data) { // TODO: Fix static URL
            var workers = data.workers;
            cb(workers);
        });
    };

    return {
        'getQueues': getQueues,
        'getJobs': getJobs,
        'getWorkers': getWorkers
    };

});
