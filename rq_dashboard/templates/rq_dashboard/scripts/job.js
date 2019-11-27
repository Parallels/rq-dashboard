(function($) {
    var $job_tpl = $('script[name=job-info]').html();
    var template = _.template($job_tpl);
    var $job_data = $('#job-data');
    var job_id = {{ id|tojson|safe }};
    var html;

    var reload_table = function(done) {
        api.getJob({{ id|tojson|safe }}, function(job, err) {
            if (err) {
                return done();
            }
            onJobLoaded(job, done);
        });

        if (done !== undefined) {
            done();
        }
    };

    var onJobLoaded = function(job, done) {
        var html = '';

        $job_data.empty();

        job.created_at = toRelative(Date.create(job.created_at)) + ' / ' + toShort(Date.create(job.created_at));
        if (job.enqueued_at !== undefined) {
            job.enqueued_at = toRelative(Date.create(job.enqueued_at)) + ' / ' + toShort(Date.create(job.enqueued_at));
        }
        if (job.ended_at !== undefined) {
            job.ended_at = toRelative(Date.create(job.ended_at)) + ' / ' + toShort(Date.create(job.ended_at));
        }
        html += template({d: job}, {variable: 'd'});
        $job_data[0].innerHTML = html;
    };

    var refresh_table_loop = function() {
        reload_table(function() {
            setTimeout(refresh_table_loop, POLL_INTERVAL);
        });
    };

    $(document).ready(function() {
        refresh_table_loop();
        $('#refresh-button').click(reload_table);
    });

    $("#cancel-job-btn").click(function() {
        var url = url_for('cancel_job', job_id);
        console.log('cancel ok');

        modalConfirm('cancel job', function() {
            $.post(url);
            $(location).attr("href", '/view/queues');
        });

        return false;
    });

    $("#requeue-job-btn").click (function() {
        var url = url_for('requeue_job', job_id);

        $.post(url);

        return false;
    });

})($);
