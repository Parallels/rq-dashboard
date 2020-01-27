(function($) {
    var $job_tpl = $('script[name=job-info]').html();
    var template = _.template($job_tpl);
    var $job_data = $('#job-data');
    var job_id = {{ id|tojson|safe }};
    var html;

    var reload_job_info = function(done) {
        api.getJob({{ id|tojson|safe }}, function(job, err) {
            if (err) {
                return done();
            }
            onJobLoaded(job, done);
        });
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
        if (job.status === "failed") {
            $("#requeue-job-btn").show()
        }
        html += template({d: job}, {variable: 'd'});
        $job_data[0].innerHTML = html;

        if (done !== undefined) {
            done();
        }
    };

    var refresh_loop = function() {
        if (AUTOREFRESH_FLAG) {
            reload_job_info(function() {
                setTimeout(refresh_loop, POLL_INTERVAL);
            });
        } else {
            setTimeout(refresh_loop, POLL_INTERVAL);
        }
    };

    $(document).ready(function() {
        refresh_loop();
        $('#refresh-button').click(reload_job_info);
    });

    $("#delete-job-btn").click(function() {
        var url = url_for('delete_job', job_id);

        modalConfirm('delete job', function() {
            $.post(url, {}, function(){
                $(location).attr("href", url_for('queues_view'));
            });
        });
        return false;
    });

    $("#requeue-job-btn").click (function() {
        var url = url_for('requeue_job', job_id);

        $.post(url);

        return false;
    });

})($);
