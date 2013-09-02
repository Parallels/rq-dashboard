

//
// QUEUES
//
(function($) {
    var reload_table = function(done) {
        var $raw_queue_tpl = $('script[name=queue-row]').html();
        var $raw_job_name_tpl = $('script[name=job-name-row]').html();
        var queue_template = _.template($raw_queue_tpl);
        var job_name_template = _.template($raw_job_name_tpl);

        var $queues_tbody = $('table#queues tbody');
        var $jobs_names_tbody = $('table#jobs-names tbody');

        $('tr[data-role=loading-placeholder]', $queues_tbody, $jobs_names_tbody).show();

        // Fetch the available queues
        api.getQueues(function(queues) {
            $queues_tbody.empty();
            $jobs_names_tbody.empty();

            if (queues.length > 0) {
                var $fq;
                queues.sort(function(a, b){ return(a.name > b.name); });
                $.each(queues, function(i, queue) {

                  var html, $tbody;
                    if (queue.name.match(/^tasks/)) {
                      html = job_name_template(queue);
                      $tbody = $jobs_names_tbody;
                    } else {
                      html = queue_template(queue);
                      $tbody = $queues_tbody;
                    }
                    var $el = $(html);
                    // Special markup for the failed queue
                    if (queue.name === 'failed' && queue.count > 0) {
                        $el.addClass('failed');
                        $fq = $el;
                        return;
                    }
                    $tbody.append($el);
                });

                // Append the failed queue at the end, since it's a special queue
                if ($fq !== undefined) {
                  $queues_tbody.append($fq);
                }
            } else {
                var html = $('script[name=no-queues-row]').html();
                $queues_tbody.append(html);
                html = $('script[name=no-jobs-names-row]').html();
                $jobs_names_tbody.append(html);
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

        $('#empty-all-btn').click(function(e) {
            e.preventDefault();
            e.stopPropagation();

            var $this = $(this);
            $.post($this.attr('href'), function(data) {
                reload_table();
            });

            return false;
        });

        reload_table();
        $('#refresh-button').click(refresh_table);
        setInterval(refresh_table, POLL_INTERVAL);

    });
})($);


//
// WORKERS
//
(function($) {
    var reload_table = function(done) {
        var $tbody = $('table#workers tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        // Fetch the available workers
        api.getWorkers(function(workers) {
            $tbody.empty();

            if (workers.length > 0) {
                if (GROUP_WORKERS) {
                    var $raw_tpl_grouped = $('script[name=worker-row-grouped]').html();
                    var template_grouped = _.template($raw_tpl_grouped);

                    // Group by queue list
                    var worker_groups = {};

                    $.each(workers, function(i, worker) {
                        var q = worker.queues.join(', ');
                        if (!worker_groups[q]) {
                            worker_groups[q] = {
                                "busy_count": 0,
                                "idle_count": 0,
                                "queues": worker.queues
                            };
                        }
                        if (worker.state === 'busy') {
                            worker_groups[q]["busy_count"]++;
                        } else {
                            worker_groups[q]["idle_count"]++;
                        }

                        worker_groups[q].href = false;
                        if (HEROKU_WORKERS) {
                            _.each(HEROKU_WORKERS, function(v, k) {
                                if (v==worker.queues.join(" ")) {
                                    worker_groups[q].href = "https://dashboard.heroku.com/apps/"+k;
                                }
                            });
                        }
                    });

                    $.each(worker_groups, function(q, worker) {
                        var html = template_grouped(worker);
                        var $el = $(html);
                        $tbody.append($el);
                    });

                } else {
                    var $raw_tpl = $('script[name=worker-row]').html();
                    var template = _.template($raw_tpl);

                    $.each(workers, function(i, worker) {
                        if (worker.state === 'busy') {
                            worker.state = 'play';
                        } else {
                            worker.state = 'pause';
                        }
                        var html = template(worker);
                        var $el = $(html);
                        $tbody.append($el);
                    });
                }

            } else {
                var html = $('script[name=no-workers-row]').html();
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
})($);


//
// JOBS
//
(function($) {
    var reload_table = function(done) {
        var $raw_tpl = $('script[name=job-row]').html();
        var template = _.template($raw_tpl);

        var $tbody = $('table#jobs tbody');

        $('tr[data-role=loading-placeholder]', $tbody).show();

        var $raw_tpl_page = $('script[name=page-link]').html();
        var template_page = _.template($raw_tpl_page);
        var $ul = $('div#page-selection ul');

        // get toggle mode for all the jobs
        var toggleStates = {};
        $tbody.find("[data-role=job]").each(function(idx){
          toggleStates[$(this).attr("data-job-id")] = $(this).hasClass("enlarge");
        });

        // Fetch the available jobs on the queue
        api.getJobs('{{ queue.name }}', '{{ page }}', function(jobs, pagination) {
            $tbody.empty();

            if (jobs.length > 0) {
                $.each(jobs, function(i, job) {
                    job.enlarge = toggleStates[job.id];
                    job.duration = (Date.create(job.ended_at)-Date.create(job.started_at))/1000;
                    job.created_at = toRelative(Date.create(job.created_at));
                    if (job.ended_at) {
                        job.ended_at = toRelative(Date.create(job.ended_at));
                    }
                    if (job.started_at) {
                        job.started_at = toRelative(Date.create(job.started_at));
                    }

                    var html = template(job);
                    var $el = $(html);

                    $tbody.append($el);
                });
            } else {
                var html = $('script[name=no-jobs-row]').html();
                $tbody.append(html);
            }

            $ul.empty();

            // prev page
            if (pagination.prev_page !== undefined ) {
                var $raw_tpl_prev_page = $('script[name=previous-page-link]').html();
                var template_prev_page = _.template($raw_tpl_prev_page);
                var html = template_prev_page(pagination.prev_page);
                var $el = $(html);
                $ul.append($el);
            } else {
                var html = $('script[name=no-previous-page-link]').html();
                $ul.append(html);
            }

            $.each(pagination.pages_in_window, function(i, page) {
               var html = template_page(page);
               var $el = $(html);

               // Special markup for the active page
               if (page.number === {{ page }} ) {
                   $el.addClass('active');
               }

               $ul.append($el);
           });

           // next page
           if (pagination.next_page !== undefined ) {
               var $raw_tpl_next_page = $('script[name=next-page-link]').html();
               var template_next_page = _.template($raw_tpl_next_page);
               var html = template_next_page(pagination.next_page);
               var $el = $(html);
               $ul.append($el);
           } else {
               var html = $('script[name=no-next-page-link]').html();
               $ul.append(html);
           }

            $("pre.exc_info").click(function(e){ $(this).closest("tr[data-role=job]").toggleClass("enlarge"); });

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

        $("#toggle-json-jobs").click(function(){ $("table#jobs").toggleClass("enlarge"); });
    });

    // Enable the AJAX behaviour of the buttons
    $('#empty-btn, #compact-btn, #requeue-all-btn, #cancel-all-btn').click(function(e) {
        e.preventDefault();
        e.stopPropagation();

        var $this = $(this);
        $this.attr("disabled", "disabled");
        $.post($this.attr('href'), function(data) {
          reload_table();
          $this.removeAttr("disabled");
        });

        return false;
    });

})($);
