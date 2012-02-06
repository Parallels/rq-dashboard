define(['jquery'], function($) {

    var getQueues = function(cb) {
        $.getJSON('/api/queues', function(data) {
            var queues = data.queues;
            cb(queues);
        });
    };

    var getJobs = function(queue_name, cb) {
        $.getJSON('/api/jobs/' + encodeURIComponent(queue_name), function(data) {
            var jobs = data.jobs;
            cb(jobs);
        });
    };

    var getWorkers = function(cb) {
        $.getJSON('/api/workers', function(data) {
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
