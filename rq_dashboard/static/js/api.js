define(['jquery'], function($) {

    var getQueues = function(cb) {
        $.getJSON(BASE_URL + 'queues', function(data) { // TODO: Fix static URL
            var queues = data.queues;
            cb(queues);
        });
    };

    var getJobs = function(queue_name, cb) {
        $.getJSON(BASE_URL + 'jobs/' + encodeURIComponent(queue_name), function(data) { // TODO: Fix static URL
            var jobs = data.jobs;
            cb(jobs);
        });
    };

    var getWorkers = function(cb) {
        $.getJSON(BASE_URL + 'workers', function(data) { // TODO: Fix static URL
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
