define(['jquery'], function($) {

    var getQueues = function(cb) {
        $.getJSON('/api/queues', function(data) {
            var queues = data.queues;
            cb(queues);
        });
    };

    return {
        'getQueues': getQueues
    };

});
