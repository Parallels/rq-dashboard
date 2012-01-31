define(['jquery'], function($) {

    var getQueues = function(cb) {
        $.getJSON('/api/queues', function(data) {
            var queues = data.queues;
            cb(queues);
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
        'getWorkers': getWorkers
    };

});
