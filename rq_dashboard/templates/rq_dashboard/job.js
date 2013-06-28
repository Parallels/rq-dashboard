
var url_for = function(name, param) {
    var url = BASE_URL;
    if (name == 'queues') { url = 'queues.json'; }
    else if (name == 'workers') { url = 'workers.json'; }
    else if (name == 'cancel_job') { url = 'job/' + encodeURIComponent(param) + '/cancel'; }
    else if (name == 'requeue_job') { url = 'job/' + encodeURIComponent(param) + '/requeue'; }
    return url;
};

var toRelative = function(universal_date_string) {
    var tzo = new Date().getTimezoneOffset();
    var d = Date.create(universal_date_string).rewind({ minutes: tzo });
    return d.relative();
};

var api = {
    getJob: function(job_id, cb) {
        $.getJSON(BASE_URL+"job/"+job_id+"/data.json", function(data) {
            cb(data);
        });
    }
};

//
// JOBS
//
(function($) {
    var reload_table = function(done) {
        var $raw_tpl = $('script[name=job-row]').html();
        var template = _.template($raw_tpl);

        var $tbody = $('table#jobs tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available jobs on the queue
        api.getJob('{{ job_id }}', function(job) {
            $tbody.empty();

            var jobs = [job];

            if (job && jobs.length > 0) {
                $.each(jobs, function(i, job) {
                    job.created_at = toRelative(Date.create(job.created_at));
                    if (job.ended_at !== undefined) {
                        job.ended_at = toRelative(Date.create(job.ended_at));
                    }
                    var html = template(job);
                    var $el = $(html);

                    $tbody.append($el);
                });
            } else {
                var html = $('script[name=no-jobs-row]').html();
                $tbody.append(html);
            }

            if (done !== undefined) {
                done();
            }
        });
    };

    var refresh_table = function() {
        $('span.loading').fadeIn('fast');
        reload_table(function() {
            $('span.loading').fadeOut('fast');
        });
    };

    $(document).ready(function() {

        reload_table();
        $('#refresh-button').click(refresh_table);
        setInterval(refresh_table, POLL_INTERVAL);

    });

    // Enable the AJAX behaviour of the empty button
    $('[data-role=cancel-job-btn]').live('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.closest('tr'),
            job_id = $row.data('job-id'),
            url = url_for('cancel_job', job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.delete(); });
        });

        return false;
    });

    // Enable the AJAX behaviour of the requeue button
    $('[data-role=requeue-job-btn]').live('click', function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this),
            $row = $this.closest('tr'),
            job_id = $row.data('job-id'),
            url = url_for('requeue_job', job_id);

        $.post(url, function(data) {
            $row.fadeOut('fast', function() { $row.delete(); });
        });

        return false;
    });

})($);
