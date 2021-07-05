angular.module('project_questions')

.factory('QuestionsService', ['$resource', '$http', '$timeout', '$location', '$rootScope', '$filter', '$q', '$window', '$sce', function($resource, $http, $timeout, $location, $rootScope, $filter, $q, $window, $sce) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        projects: $resource(baseurl + 'api/v1/projects/projects/:id/:detail_action/'),
        values: $resource(baseurl + 'api/v1/projects/projects/:project/values/:id/'),
        questionsets: $resource(baseurl + 'api/v1/projects/projects/:project/questionsets/:list_action/:id/'),
        settings: $resource(baseurl + 'api/v1/core/settings/')
    };

    /* configure factories */

    var factories = {
        values: function(question) {
            return {
                text: question.default_text,
                option: question.default_option,
                external_id: question.default_external_id,
                file: null,
                project: service.project.id,
                attribute: question.attribute,
                changed: (question.default_text || question.default_option || question.default_external_id),
                removed: false
            };
        },
        valuesets: function(set_prefix, set_index) {
            return {
                set_prefix: set_prefix,
                set_index: set_index,
                hidden: {
                    questionsets: {},
                    questions: {},
                    optionsets: {}
                },
                removed: false
            };
        }
    };

    /* create a buffer for the future service content */

    var future = {};

    /* create a flag to be used when clicking the prev button */

    var back = false;

    /* create a flag to be used when the view is initializing */

    var initializing = false;

    /* create a flag to debounce search requests */

    var searching = false;

    /* create the questions service */

    var service = {
        set_prefix: '',
        set_index: null,
        values: null
    };

    service.init = function(project_id) {
        service.settings = resources.settings.get();
        service.project = resources.projects.get({id: project_id, detail_action: 'overview'});

        $q.all([
            service.settings.$promise,
            service.project.$promise
        ]).then(function() {
            // get the current questionset_id form the url
            var questionset_id = $location.path().replace(/\//g,'');

            // init the view
            service.initView(questionset_id).then(function() {
                // enable back/forward button of browser
                $rootScope.$on('$locationChangeSuccess', function (scope, next, current) {
                    var questionset_id = parseInt($location.path().replace(/\//g,''), 10);
                    if (questionset_id !== service.questionset.id) {
                        service.initView(questionset_id);
                    }
                });
            });

            $window.addEventListener('beforeunload', function(event) {
                var changed = false, removed = false;;
                angular.forEach(service.values, function(sets) {
                    angular.forEach(sets, function(set) {
                        angular.forEach(set, function(values) {
                            angular.forEach(values, function(value) {
                                if (angular.isDefined(value.changed) && value.changed) {
                                    changed = true;
                                }
                            });
                        });
                    });
                });

                if (changed || removed) {
                    event.preventDefault();
                    return event.returnValue = 'You have unsaved changes.';
                }
            });
        });
    };

    service.initView = function(questionset_id) {
        if (initializing) return;

        if (questionset_id !== null) {
            // enable initializing flag
            initializing = true;

            return service.fetchQuestionSet(questionset_id)
            .then(service.fetchOptions)
            .then(service.fetchValues)
            .then(service.fetchConditions)
            .then(function () {
                // copy future objects
                angular.forEach([
                    'questionset', 'progress', 'attributes', 'questionsets', 'questions', 'valuesets', 'values'
                ], function (key) {
                    service[key] = angular.copy(future[key]);
                });

                // activate fist valueset
                if (angular.isDefined(service.valuesets[service.questionset.id][service.set_prefix])) {
                    service.set_index = service.valuesets[service.questionset.id][service.set_prefix][0].set_index;
                } else {
                    service.set_index = null;
                }

                // focus the first field
                if (service.values && Object.keys(service.values).length && service.questionset.questionsets.length == 0) {
                    var first_question = service.questionset.questions[0];
                    if (['text', 'textarea'].indexOf(first_question.widget_type) > -1) {
                        service.focusField(first_question.attribute, service.set_prefix, service.set_index, 0);
                    }
                }

                // disable initializing flag again
                initializing = false;

                // set browser location, scroll to top and set back flag
                $location.path('/' + service.questionset.id + '/');
                $window.scrollTo(0, 0);
                back = false;

                $timeout(function() {
                    $('[data-toggle="tooltip"]').tooltip();
                });
            }, function (result) {
                // disable initializing flag again
                initializing = false;

                // re-init without questionset
                return service.initView('');
            });
        } else {
            service.questionset = {
                id: false,
                progress: 100,
                next: null,
                prev: service.questionset ? service.questionset.id : null
            };

            // set browser location, scroll to top and set back flag
            // $location.path('/done/');
            $window.scrollTo(0, 0);
            back = false;
        }
    };

    service.fetchQuestionSet = function(questionset_id) {

        // fetch the current (or the first) question set from the server
        if (questionset_id) {
            future.questionset = resources.questionsets.get({project: service.project.id, id: questionset_id});
        } else {
            future.questionset = resources.questionsets.get({
                project: service.project.id,
                list_action: 'continue'
            });
        }

        // store the questionset and return the promise
        return future.questionset.$promise.then(function() {
            // init attributes, questionsets, and questions array
            future.attributes = [];
            future.questionsets = [];
            future.questions = [];

            // loop over all elements
            // (a) create seperate questions array
            // (b) mark the help text of the question set 'save'
            // (c) sort questionsets and questions by order in one list called elements
            // using recursive functions!
            service.initQuestionSet(future.questionset);
        });
    };

    service.initQuestionSet = function(questionset) {
        // store attributes and questionset in seperate array
        if (questionset.attribute !== null) {
            future.attributes.push(questionset.attribute);
        }
        future.questionsets.push(questionset);

        // mark the help text of the question set 'save'
        questionset.help = $sce.trustAsHtml(questionset.help);

        // sort questionsets and questions by order in one list called elements
        questionset.elements = questionset.questionsets.map(function(qs) {
                return service.initQuestionSet(qs);
            })
            .concat(questionset.questions.map(service.initQuestion))
            .sort(function(a, b) { return a.order - b.order; });

        return questionset;
    };

    service.initQuestion = function(question) {
        // store attributes and questionset in seperate array
        if (question.attribute !== null) {
            future.attributes.push(question.attribute);
        }
        future.questions.push(question);

        // mark the help text of the question set 'save'
        question.help = $sce.trustAsHtml(question.help);

        // this is a question!
        question.isQuestion = true;

        return question;
    };

    service.fetchOptions = function() {
        promises = [];

        angular.forEach(future.questions, function(question) {
            if (question.optionsets.length) {
                // init options array for this questions attribute
                question.options = [];

                angular.forEach(question.optionsets, function(optionset) {
                    if (optionset.has_provider) {
                        // call the provider to get addtional options
                        promises.push(resources.projects.query({
                            detail_action: 'options',
                            optionset: optionset.id,
                            id: service.project.id,
                        }, function(response) {
                            question.options = question.options.concat(response.map(function(option) {
                                option.has_provider = optionset.has_provider
                                return option
                            }));

                            // if any, add regular options from the optionset
                            if (question.optionsets.options !== false) {
                                question.options = question.options.concat(optionset.options);
                            }
                        }).$promise);
                    } else {
                        question.options = question.options.concat(optionset.options);
                    }
                });
            }
        });

        return $q.all(promises);
    };

    service.fetchValues = function() {
        var promises = [];

        // fetch current progress for this project
        promises.push(resources.projects.get({
            id: service.project.id,
            detail_action: 'progress'
        }, function(response) {
            future.progress = response;
        }).$promise);

        // fetch all values for the set from the server
        promises.push(resources.values.query({
            project: service.project.id,
            attribute: future.attributes
        }, function(response) {
            // init values
            future.values = {};

            // loop over all values to sort them by attribute -> set_prefix -> set_index -> collection_index
            angular.forEach(response, function(value) {
                // add an object for each attribute found
                if (angular.isUndefined(future.values[value.attribute])) {
                    future.values[value.attribute] = {};
                }
                // add an object for each set_prefix found
                if (angular.isUndefined(future.values[value.attribute][value.set_prefix])) {
                    future.values[value.attribute][value.set_prefix] = {};
                }
                // add an array for each (new) set_index found
                if (angular.isUndefined(future.values[value.attribute][value.set_prefix][value.set_index])) {
                    future.values[value.attribute][value.set_prefix][value.set_index] = [];
                }
                // push the value, the collection_index might be off but this is intended to close gaps
                future.values[value.attribute][value.set_prefix][value.set_index].push(value);
            });

            // init valuesets
            future.valuesets = {};

            // loop over all questionsets to initlize valuesets
            // valuesets store the set_index for each questionset and set_prefix
            angular.forEach(future.questionsets, function(questionset) {
                // add a valueset for each questionset
                if (angular.isUndefined(future.valuesets[questionset.id])) {
                    future.valuesets[questionset.id] = {};
                }

                // add the set_index for every value for the attribute of this questionset
                angular.forEach(future.values[questionset.attribute], function(sets, set_prefix) {
                    if (angular.isUndefined(future.valuesets[questionset.id][set_prefix])) {
                        future.valuesets[questionset.id][set_prefix] = [];
                    }
                    angular.forEach(sets, function(set, set_index) {
                        var valuesets = $filter('filter')(future.valuesets[questionset.id][set_prefix], function(valueset) {
                            return (valueset.set_prefix == set_prefix) && (valueset.set_index == set_index);
                        });
                        if (valuesets.length === 0) {
                            future.valuesets[questionset.id][set_prefix].push(factories.valuesets(set_prefix, set_index))
                        }
                    });
                });

                // add the set_index for every value for the attribute of each question of this questionset
                angular.forEach(questionset.questions, function(question) {
                    angular.forEach(future.values[question.attribute], function(sets, set_prefix) {
                        if (angular.isUndefined(future.valuesets[questionset.id][set_prefix])) {
                            future.valuesets[questionset.id][set_prefix] = [];
                        }
                        angular.forEach(sets, function(set, set_index) {
                            var valuesets = $filter('filter')(future.valuesets[questionset.id][set_prefix], function(valueset) {
                                return (valueset.set_prefix == set_prefix) && (valueset.set_index == set_index);
                            });
                            if (valuesets.length === 0) {
                                future.valuesets[questionset.id][set_prefix].push(factories.valuesets(set_prefix, set_index))
                            }
                        });
                    });
                });

                // sort valuesets
                angular.forEach(future.valuesets[questionset.id], function(valuesets, set_prefix) {
                    valuesets.sort(function(a, b) { return a.set_index - b.set_index; });
                });
            });
        }).$promise);

        return $q.all(promises).then(function() {
            service.initValues(future.questionset, '');
        });
    };

    service.fetchConditions = function() {
        promises = [];

        // check conditions for current questionsets and questions
        angular.forEach(future.questionsets, function(questionset) {
            angular.forEach(future.valuesets[questionset.id], function(valuesets, set_prefix) {
                angular.forEach(valuesets, function(valueset, set_index) {
                    angular.forEach(questionset.questionsets, function(qs) {
                        if (qs.has_conditions) {
                            promises.push(resources.projects.get({
                                id: service.project.id,
                                detail_action: 'resolve',
                                questionset: qs.id,
                                set_prefix: set_prefix,
                                set_index: set_index
                            }, function(response) {
                                valueset.hidden.questionsets[qs.id] = !response.result;
                            }).$promise);
                        }
                    });
                    angular.forEach(questionset.questions, function(q) {
                        if (q.has_conditions) {
                            promises.push(resources.projects.get({
                                id: service.project.id,
                                detail_action: 'resolve',
                                question: q.id,
                                set_prefix: set_prefix,
                                set_index: set_index
                            }, function(response) {
                                valueset.hidden.questions[q.id] = !response.result;
                            }).$promise);
                        }

                        angular.forEach(q.optionsets, function(optionset) {
                            if (optionset.has_conditions) {
                                promises.push(resources.projects.get({
                                    id: service.project.id,
                                    detail_action: 'resolve',
                                    optionset: optionset.id,
                                    set_prefix: set_prefix,
                                    set_index: set_index
                                }, function(response) {
                                    valueset.hidden.optionsets[optionset.id] = !response.result;
                                }).$promise);
                            }
                        });
                    });
                });
            });
        });

        return $q.all(promises);
    };

    service.initValues = function(questionset, set_prefix) {
        // for non collection questionsets create at least one valueset (for this set_prefix)
        if (!questionset.is_collection) {
            if (angular.isUndefined(future.valuesets[questionset.id])) {
                future.valuesets[questionset.id] = {};
            }
            if (angular.isUndefined(future.valuesets[questionset.id][set_prefix])) {
                future.valuesets[questionset.id][set_prefix] = [factories.valuesets(set_prefix, 0)];
            }
        }

        // loop over valuesets and initialize at leat one value for each question
        angular.forEach(future.valuesets[questionset.id][set_prefix], function(valueset) {
            // loop over questions to initialize them with at least one value, and init checkboxes and widgets
            angular.forEach(questionset.questions, function(question) {
                if (angular.isUndefined(future.values[question.attribute])) {
                    future.values[question.attribute] = {};
                }
                if (angular.isUndefined(future.values[question.attribute][set_prefix])) {
                    future.values[question.attribute][set_prefix] = {};
                }
                if (angular.isUndefined(future.values[question.attribute][set_prefix][valueset.set_index])) {
                    future.values[question.attribute][set_prefix][valueset.set_index] = [];
                }
                if (angular.isUndefined(future.values[question.attribute][set_prefix][valueset.set_index][0])) {
                    future.values[question.attribute][set_prefix][valueset.set_index].push(factories.values(question));
                }

                // for a checkbox, transform the values for the question to different checkboxes
                if (question.widget_type === 'checkbox') {
                    future.values[question.attribute][valueset.set_prefix][valueset.set_index] = service.initCheckbox(question, future.values[question.attribute][valueset.set_prefix][valueset.set_index]);
                }

                angular.forEach(future.values[question.attribute][valueset.set_prefix][valueset.set_index], function(value) {
                    service.initWidget(question, value);
                });
            });
        });

        // recursively loop over child questionsets and sets
        angular.forEach(questionset.questionsets, function(qs) {
            angular.forEach(future.valuesets[questionset.id][set_prefix], function(valueset, set_index) {
                service.initValues(qs, service.joinSetPrefix(set_prefix, set_index));
            });
        });
    };

    service.initWidget = function(question, value) {
        // for radio, select, and autocomplete:
        // value.selected is set to value.option or value.external_id and then used as model by the widget
        // it needs to be a string in order to use the same select widget in both cases
        if (question.widget_type === 'radio' ||
            question.widget_type === 'select' ||
            question.widget_type === 'autocomplete') {

            value.selected = '';
            angular.forEach(question.options, function(option) {
                if ((value.selected === '') &&
                    (option.has_provider && option.id === value.external_id || option.id === value.option)) {

                    value.selected = option.id.toString();
                }
            })
        }

        // for radio and checkboxes:
        // value.additional_input is used to hold the text for additional input
        if (question.widget_type === 'radio' ||
            question.widget_type === 'checkbox') {

            value.additional_input = {};

            angular.forEach(question.options, function(option) {
                if (!option.has_provider && option.additional_input && value.option === option.id) {
                    value.additional_input[option.id] = value.text;
                }
            });
        }

        // for range:
        // the widget is initialized to 0
        if (question.widget_type === 'range') {
            if (!value.text) {
                value.text = '0';
            }
        }

        // for autocomplete
        // fuse in initalized and the widget is locked for existing values
        if (question.widget_type === 'autocomplete') {
            if (angular.isArray(question.options)) {
                question.options_fuse = new Fuse(question.options, {
                    keys: ['text']
                });
            }

            if (value.option) {
                value.autocomplete_locked = false;
                angular.forEach(question.options, function(option) {
                    if (value.autocomplete_locked === false && option.id === value.option) {
                        value.autocomplete_locked = true;
                        value.autocomplete_input = option.text;
                        value.autocomplete_text = option.text;
                    }
                });
            } else if (value.text) {
                value.autocomplete_locked = true;
                value.autocomplete_input = value.text;
                value.autocomplete_text = value.text;
            }
        }
    };

    service.initCheckbox = function(question, values) {
        var checkbox_values = [];

        angular.forEach(question.options, function(option) {
            var filter = $filter('filter')(values, function(value, index, array) {
                if (option.has_provider && option.id == value.external_id) {
                    return true
                } else if (value.option && option.id == value.option) {
                    return true
                }
            });

            var value;
            if (filter.length === 1) {
                // found an existing value
                value = filter[0];
                value.removed = false;
            } else {
                // create a new value for this option
                value = factories.values(question);
                value.removed = true;
            }

            if (option.has_provider) {
                value.selected = option.id;
            } else {
                value.selected = option.id.toString();
            }

            checkbox_values.push(value);
        });

        return checkbox_values;
    };

    service.focusField = function(attribute, set_prefix, set_index, collection_index) {
        $timeout(function() {
            if (angular.isDefined(attribute) &&
                angular.isDefined(set_prefix) &&
                angular.isDefined(set_index) &&
                angular.isDefined(collection_index)) {

                angular.element('#id_' + attribute.toString() + '_' +
                                         set_prefix.toString() + '_' +
                                         set_index.toString() + '_' +
                                         collection_index.toString()).focus();
            }
        });
    };

    service.storeValue = function(value, question, set_prefix, set_index, collection_index) {
        if (angular.isDefined(value.removed) && value.removed) {
            // remove additional_input from unselected checkboxes
            value.additional_input = {};

            // delete the value if it alredy exists on the server
            if (angular.isDefined(value.id)) {
                return resources.values.delete({
                    id: value.id,
                    project: service.project.id
                }, function() {
                    value.changed = false;
                }).$promise;
            } else {
                value.changed = false;
            }

        } else {
            // store the current index in the list
            value.set_prefix = set_prefix;
            value.set_index = set_index;
            value.collection_index = collection_index;

            // get value_type and unit from question
            if (question === null) {
                // this is the id of a new valueset
                value.value_type = 'text';
                value.unit = '';
            } else {
                value.value_type = question.value_type;
                value.unit = question.unit;
            }

            if (angular.isDefined(value.selected) && value.selected) {
                // set everything empty by default
                value.text = '';
                value.option = null;
                value.external_id = '';

                if (angular.isDefined(value.autocomplete_search) && value.autocomplete_search) {
                    value.text = value.autocomplete_text;
                    value.external_id = value.selected;
                } else {
                    // loop over options
                    angular.forEach(question.options, function(option) {
                        if (option.has_provider && value.selected === option.id) {
                            value.text = option.text;
                            value.external_id = option.id;
                        } else if (value.selected === option.id.toString()) {
                            // get text from additional_input for the selected option
                            if (angular.isDefined(value.additional_input) && angular.isDefined(value.additional_input[option.id])) {
                                value.text = value.additional_input[option.id];
                            }

                            // cast value.selected back to int
                            value.option = parseInt(option.id, 10);
                        } else {
                            // remove additional_input from unselected options
                            if (angular.isDefined(value.additional_input) && angular.isDefined(value.additional_input[option.id])) {
                                delete value.additional_input[option.id];
                            }
                        }
                    });
                }
            } else {
                // set value.option and value.external_id empty by default
                value.option = null;
                value.external_id = '';
            }

            var promise;
            if (angular.isDefined(value.id)) {
                // update an existing value
                promise = resources.values.update({
                    id: value.id,
                    project: service.project.id
                }, value).$promise;
            } else {
                // update a new value
                promise = resources.values.save({
                    project: service.project.id
                }, value).$promise;
            }

            return promise.then(function(response) {
                if (angular.isDefined(value.file) && value.file !== null) {
                    value.errors = []

                    // upload file after the value is created
                    var url = baseurl + 'api/v1/projects/projects/' + service.project.id + '/values/' + response.id + '/file/';
                    var formData = new FormData();
                    formData.append('file', value.file);

                    return $http({
                        url: url,
                        method: 'POST',
                        data: formData,
                        headers: {'Content-Type': undefined}
                    }).success(function (response) {
                        response.file = null;
                        angular.extend(value, response);
                        value.changed = false;
                    }).error(function (response) {
                        value.errors = response.value;
                    });
                } else {
                    angular.extend(value, response);
                    value.changed = false;
                }
            }, function (response) {
                value.errors = response.data.value;
            })
        }
    };

    service.storeValues = function() {
        var promises = [];

        angular.forEach(service.questions, function(question) {
            angular.forEach(service.values[question.attribute], function(set, set_prefix) {
                angular.forEach(set, function(values, set_index) {
                    angular.forEach(values, function(value, collection_index) {
                        if (angular.isDefined(value.changed) && value.changed) {
                            promises.push(service.storeValue(value, question, set_prefix, set_index, collection_index));
                        }
                    });
                });
            });
        });

        return $q.all(promises);
    };

    service.prev = function() {
        if (service.questionset.prev !== null) {
            back = true;
            service.initView(service.questionset.prev);
        }
    };

    service.next = function() {
        if (service.questionset.id !== null) {
            service.initView(service.questionset.next);
        }
    };

    service.jump = function(section, questionset) {
        if (service.settings.project_questions_autosave) {
            service.save(false).then(function() {
                if (angular.isDefined(questionset)) {
                    service.initView(questionset.id);
                } else if (angular.isDefined(section)) {
                    service.initView(section.questionsets[0].id);
                } else {
                    service.initView(null);
                }
            });
        } else {
            if (angular.isDefined(questionset)) {
                service.initView(questionset.id);
            } else if (angular.isDefined(section)) {
                service.initView(section.questionsets[0].id);
            } else {
                service.initView(null);
            }
        }
    };

    service.save = function(proceed) {
        return service.storeValues().then(function() {
            if (angular.isDefined(proceed) && proceed) {
                if (service.questionset.is_collection) {
                    if (service.set_index === null) {
                        service.next();
                    } else {
                        var valuesets = service.valuesets[service.questionset.id][service.set_prefix];
                        var index = service.findIndex(valuesets, 'set_index', service.set_index);

                        if (index === valuesets.length - 1) {
                            // this is the last valueset, go to the next page
                            service.next();
                        } else {
                            // activate the next valueset
                            service.set_index = valuesets[index + 1].set_index;
                            $window.scrollTo(0, 0);
                        }
                    }
                } else {
                    service.next();
                }
            } else {
                // update progress
                resources.projects.get({
                    id: service.project.id,
                    detail_action: 'progress'
                }, function(response) {
                    if (service.progress.values != response.values) {
                        service.progress = response
                    }
                });

                // re-evaluate conditions
                angular.forEach(service.questionsets, function(questionset) {
                    angular.forEach(service.valuesets[questionset.id], function(valuesets, set_prefix) {
                        angular.forEach(valuesets, function(valueset, set_index) {
                            angular.forEach(questionset.questionsets, function(qs) {
                                if (qs.has_conditions) {
                                    promises.push(resources.projects.get({
                                        id: service.project.id,
                                        detail_action: 'resolve',
                                        questionset: qs.id,
                                        set_prefix: set_prefix,
                                        set_index: set_index
                                    }, function(response) {
                                        valueset.hidden.questionsets[qs.id] = !response.result;
                                    }).$promise);
                                }
                            });
                            angular.forEach(questionset.questions, function(q) {
                                if (q.has_conditions) {
                                    promises.push(resources.projects.get({
                                        id: service.project.id,
                                        detail_action: 'resolve',
                                        question: q.id,
                                        set_prefix: set_prefix,
                                        set_index: set_index
                                    }, function(response) {
                                        valueset.hidden.questions[q.id] = !response.result;
                                    }).$promise);
                                }
                                angular.forEach(q.optionsets, function(optionset) {
                                    if (optionset.has_conditions) {
                                        promises.push(resources.projects.get({
                                            id: service.project.id,
                                            detail_action: 'resolve',
                                            optionset: optionset.id,
                                            set_prefix: set_prefix,
                                            set_index: set_index
                                        }, function(response) {
                                            valueset.hidden.optionsets[optionset.id] = !response.result;
                                        }).$promise);
                                    }
                                });
                            });
                        });
                    });
                });
            }
        });
    };

    service.changed = function(value, autosave=false) {
        value.changed = true;

        if (service.settings.project_questions_autosave && autosave) {
            service.save();
        }
    };

    service.addValue = function(question, set_prefix, set_index) {
        var value = factories.values(question);

        //  add new value to service.values
        if (angular.isUndefined(service.values[question.attribute][set_prefix][set_index])) {
            service.values[question.attribute][set_prefix][set_index] = [value];
        } else {
            service.values[question.attribute][set_prefix][set_index].push(value);
        }

        // initialize widgets like in service.initValues
        service.initWidget(question, value);

        // focus the new value
        var collection_index = service.values[question.attribute][set_prefix][set_index].length - 1;
        service.focusField(question.attribute, set_prefix, set_index, collection_index);
    };

    service.eraseValue = function(attribute, set_prefix, set_index, collection_index) {
        service.values[attribute][set_prefix][set_index][collection_index].text = '';
        service.values[attribute][set_prefix][set_index][collection_index].additional_input = {};
        service.values[attribute][set_prefix][set_index][collection_index].file_url = null;
        service.values[attribute][set_prefix][set_index][collection_index].file = false;
        service.values[attribute][set_prefix][set_index][collection_index].selected = '';
        service.values[attribute][set_prefix][set_index][collection_index].autocomplete_input = '';
        service.values[attribute][set_prefix][set_index][collection_index].autocomplete_text = '';
        service.values[attribute][set_prefix][set_index][collection_index].autocomplete_locked = false;
        service.values[attribute][set_prefix][set_index][collection_index].changed = true;
    };

    service.removeValue = function(attribute, set_prefix, set_index, collection_index) {
        service.values[attribute][set_prefix][set_index][collection_index].removed = true;
        service.values[attribute][set_prefix][set_index][collection_index].changed = true;
    };

    service.openValueSetFormModal = function(questionset, set_prefix, set_index) {
        service.modal_values = {};
        service.modal_errors = {};

        if (questionset.attribute) {
            if (angular.isDefined(set_index)) {
                // get the existing title if there is a value for that
                if (angular.isDefined(service.values[questionset.attribute]) &&
                    angular.isDefined(service.values[questionset.attribute][set_prefix]) &&
                    angular.isDefined(service.values[questionset.attribute][set_prefix][set_index]) &&
                    angular.isDefined(service.values[questionset.attribute][set_prefix][set_index][0])) {

                    service.modal_values = angular.copy(service.values[questionset.attribute][set_prefix][set_index][0]);
                }
            }

            service.modal_values.questionset = questionset;
            service.modal_values.set_prefix = set_prefix;
            service.modal_values.set_index = set_index;

            $timeout(function() {
                $('#valuesets-form-modal').modal('show');
                $('#modal-title-input').focus();
            });
        } else {
            service.addValueSet(questionset, set_prefix, set_index);
        }
    };

    service.submitValueSetFormModal = function() {
        service.modal_errors = {};

        // validate that there is any title given
        if (service.modal_values.questionset.attribute) {
            if (angular.isUndefined(service.modal_values.text) || !service.modal_values.text) {
                service.modal_errors.text = [];
                return;
            }
        }

        // create a new valueset if the create flag was set
        if (angular.isDefined(service.modal_values.set_index)) {
            service.updateValueSet(service.modal_values.questionset,
                                   service.modal_values.set_prefix,
                                   service.modal_values.set_index,
                                   service.modal_values.text);
        } else {
            service.addValueSet(service.modal_values.questionset,
                                service.modal_values.set_prefix,
                                service.modal_values.text);
        }

        $timeout(function() {
            $('#valuesets-form-modal').modal('hide');
        });
    };

    service.openValueSetDeleteModal = function(questionset, set_prefix, set_index) {
        service.modal_values = {};
        service.modal_values.questionset = questionset;
        service.modal_values.set_prefix = set_prefix;
        service.modal_values.set_index = set_index;

        $timeout(function() {
            $('#valuesets-delete-modal').modal('show');
        });
    };

    service.submitValueSetDeleteModal = function() {
        service.removeValueSet(service.modal_values.questionset,
                               service.modal_values.set_prefix,
                               service.modal_values.set_index);

        $timeout(function() {
            $('#valuesets-delete-modal').modal('hide');
        });
    };

    service.activateValueSet = function(set_prefix) {
        if (service.settings.project_questions_autosave) {
            service.save(false).then(function() {
                service.set_index = set_prefix;
            });
        } else {
            service.set_index = set_prefix;
        }
    };

    service.addValueSet = function(questionset, set_prefix, text) {
        var set_index = 0;

        // get the new set_index and append it to the array of valuesets
        if (angular.isUndefined(service.valuesets[questionset.id][set_prefix])) {
            service.valuesets[questionset.id][set_prefix] = [];
        }
        if (service.valuesets[questionset.id][set_prefix].length > 0) {
            var valuesets = $filter('orderBy')(service.valuesets[questionset.id][set_prefix], '-set_index');
            var last_set_index = valuesets[0].set_index;
            set_index = parseInt(last_set_index) + 1;
        }
        service.valuesets[questionset.id][set_prefix].push(factories.valuesets(set_prefix, set_index));

        // loop over questions to initialize them with at least one value, and init checkboxes and widgets
        angular.forEach(questionset.questions, function(question) {
            if (angular.isUndefined(service.values[question.attribute])) {
                service.values[question.attribute] = {};
            }
            if (angular.isUndefined(service.values[question.attribute][set_prefix])) {
                service.values[question.attribute][set_prefix] = {};
            }
            if (angular.isUndefined(service.values[question.attribute][set_prefix][set_index])) {
                service.values[question.attribute][set_prefix][set_index] = [];
            }
            if (angular.isUndefined(service.values[question.attribute][set_prefix][set_index][0])) {
                service.values[question.attribute][set_prefix][set_index].push(factories.values(question));
            }

            // for a checkbox, transform the values for the question to different checkboxes
            if (question.widget_type === 'checkbox') {
                service.values[question.attribute][set_prefix][set_index] = service.initCheckbox(question, service.values[question.attribute][set_prefix][set_index]);
            }

            angular.forEach(service.values[question.attribute][set_prefix][set_index], function(value) {
                service.initWidget(question, value);
            });
        });

        if (angular.isDefined(text) && questionset.attribute) {
            // create a value to hold the id of the valuset
            var value = {
                project: service.project.id,
                attribute: questionset.attribute,
                text: text
            };

            if (angular.isUndefined(service.values[questionset.attribute])) {
                service.values[questionset.attribute] = {};
            }
            if (angular.isUndefined(service.values[questionset.attribute][set_prefix])) {
                service.values[questionset.attribute][set_prefix] = {};
            }
            if (angular.isUndefined(service.values[questionset.attribute][set_prefix][set_index])) {
                service.values[questionset.attribute][set_prefix][set_index] = [];
            }
            if (angular.isUndefined(service.values[questionset.attribute][set_prefix][set_index][0])) {
                service.values[questionset.attribute][set_prefix][set_index].push(value);
            }
            service.storeValue(value, null, set_prefix, set_index, 0)
        }

        // recursively loop over child questionsets and sets
        angular.forEach(questionset.questionsets, function(qs) {
            // for non collection questionsets create at least one valueset
            if (!qs.is_collection) {
                service.addValueSet(qs, service.joinSetPrefix(set_prefix, set_index));
            }
        });

        // switch set_index if this is the top level questionset
        if (questionset == service.questionset) {
            service.set_index = set_index;
        }
    };

    service.updateValueSet = function(questionset, set_prefix, set_index, text) {
        // create a value to hold the id of the valuset if it does not exist yet
        if (angular.isUndefined(service.values[questionset.attribute])) {
            service.values[questionset.attribute] = {};
        }
        if (angular.isUndefined(service.values[questionset.attribute][set_prefix])) {
            service.values[questionset.attribute][set_prefix] = {};
        }
        if (angular.isUndefined(service.values[questionset.attribute][set_prefix][set_index])) {
            service.values[questionset.attribute][set_prefix][set_index] = [];
        }
        if (angular.isUndefined(service.values[questionset.attribute][set_prefix][set_index][0])) {
            service.values[questionset.attribute][set_prefix][set_index].push({
                'project': service.project.id,
                'attribute': questionset.attribute
            });
        }

        // update the value holding the id of the valuset
        service.values[questionset.attribute][set_prefix][set_index][0].text = text;

        // store the value on the server
        service.storeValue(service.values[questionset.attribute][set_prefix][set_index][0], null, set_prefix, set_index, 0);
    };

    service.removeValueSet = function(questionset, set_prefix, set_index) {
        // delete the value for the attribute of this questionset
        if (questionset.attribute && angular.isDefined(service.values[questionset.attribute])) {
            angular.forEach(service.values[questionset.attribute][set_prefix][set_index], function(value) {
                if (angular.isDefined(value)) {
                    value.removed = true;
                    service.storeValue(value, null, set_prefix, set_index, value.collection_index);
                }
            });
        }

        // delete the values for the attribute of the questions of this questionset
        angular.forEach(questionset.questions, function(question) {
            angular.forEach(service.values[question.attribute][set_prefix][set_index], function(value) {
                if (angular.isDefined(value)) {
                    value.removed = true;
                    service.storeValue(value, null, set_prefix, set_index, value.collection_index);
                }
            });
        });

        // recursively delete questionsets of this questionset
        angular.forEach(questionset.questionsets, function(qs) {
            var sp = service.joinSetPrefix(set_prefix, set_index);

            // loop over a copy of the valueset, since elements are removed during the iteration
            angular.forEach(angular.copy(service.valuesets[qs.id][sp]), function (si) {
                service.removeValueSet(qs, sp, si);
            });
        });

        // if this is the top level questionset,
        // activate the set before the current one,
        // otherwise the previous set
        if (questionset == service.questionset) {
            // get list of valuesets which are not removed yet
            var valuesets = $filter('filter')(service.valuesets[questionset.id][set_prefix], function(valueset) {
                return valueset.removed === false;
            });

            if (valuesets.length == 1) {
                service.set_index = null;
            } else {
                var index = service.findIndex(valuesets, 'set_index', set_index);
                if (index == 0) {
                    service.set_index = valuesets[1].set_index;
                } else {
                    service.set_index = valuesets[index - 1].set_index;
                }
            }
        }

        // remove the set from valuesets
        var index = service.findIndex(service.valuesets[questionset.id][set_prefix], 'set_index', set_index);
        service.valuesets[questionset.id][set_prefix][index].removed = true;
    };

    // called when the options in the autocomplete field need to be updated
    service.filterAutocomplete = function(question, value) {
        if (value.autocomplete_input) {
            var promises = [];

            if (searching === false) {
                angular.forEach(question.optionsets, function(optionset) {
                    if (optionset.has_search) {
                        // set the searching flag
                        searching = true;

                        // call the provider to search for options
                        promises.push(resources.projects.query({
                            detail_action: 'options',
                            optionset: optionset.id,
                            id: service.project.id,
                            search: value.autocomplete_input
                        }, function(response) {
                            return response.map(function(option) {
                                option.has_provider = true;
                                return option;
                            });
                        }).$promise);
                    }
                });
            }

            if (searching) {
                if (promises.length > 0) {
                    $q.all(promises).then(function(results) {
                        // combine results to one array and set value.autocomplete_search
                        value.autocomplete_search = true;
                        value.items = results.reduce(function(items, result) {
                            return items.concat(result);
                        }, [])

                        // unset the searching flag
                        searching = false;
                    });
                }
            } else {
                // if no search was performed, do the searching on the client
                value.autocomplete_search = false;
                value.items = question.options_fuse.search(value.autocomplete_input);
            }
        } else {
            value.items = [];
        }
    };

    // called when the user uses a keyboard button while in the autocomplete field
    service.keydownAutocomplete = function(question, value, $event) {
        if (['ArrowUp', 'ArrowDown', 'Enter', 'NumpadEnter', 'Escape'].indexOf($event.code) > -1) {
            $event.preventDefault();

            var active;
            value.items.map(function (item, index) {
                if (item.active) {
                    // if by accident, two items are active, this will pick the last, which is ok
                    active = index;
                    item.active = false;
                }
            });

            if ($event.code == 'ArrowUp' || $event.code == 'ArrowDown') {
                var next;
                if ($event.code == 'ArrowUp') {
                    if (angular.isDefined(active)) {
                        next = value.items[active - 1];
                    } else {
                        next = value.items[value.items.length - 1];
                    }
                } else if ($event.code == 'ArrowDown') {
                    if (angular.isDefined(active)) {
                        next = value.items[active + 1];
                    } else {
                        next = value.items[0];
                    }
                }
                if (angular.isDefined(next)) {
                    next.active = true;
                    value.autocomplete_input = next.text;
                }
            } else if ($event.code == 'Enter' || $event.code == 'NumpadEnter') {
                if (angular.isDefined(active)) {
                    service.selectAutocomplete(value, value.items[active]);
                }
            } else if ($event.code == 'Escape') {
                if (value.selected === '') {
                    value.autocomplete_input = '';
                    service.filterAutocomplete(question, value.items[active]);
                } else {
                    value.autocomplete_locked = true;
                }
            }
        }
    };

    // called when the user clicks on an option of the autocomplete field
    service.selectAutocomplete = function(value, option) {
        value.autocomplete_locked = true;
        value.selected = option.id.toString();
        value.autocomplete_text = option.text;
    }

    // called when the user clicks outside the autocomplete field
    service.blurAutocomplete = function(value) {
        if (value.selected === '') {
            value.autocomplete_input = '';
            value.autocomplete_text = '';
            value.items = null;
        } else {
            value.autocomplete_locked = true;
            value.autocomplete_input = value.autocomplete_text;
        }
    }

    // called when the user clicks in the autocomplete field
    service.unlockAutocomplete = function(question, value, set_prefix, set_index, index) {
        value.autocomplete_locked = false;
        service.focusField(question.attribute.id, set_prefix, set_index, index);
    };

    service.isDefaultValue = function(question, value) {
        if (angular.isDefined(value.id)) {
            return false;
        }

        if (question.default_text) {
            return question.default_text == value.text;
        } else if (question.default_option) {
            return question.default_option.toString() == value.selected;
        } else if (question.default_external_id) {
            return question.default_external_id == value.selected;
        }
    }

    service.joinSetPrefix = function(set_prefix, set_index) {
        if (set_prefix === '') {
            return set_index.toString();
        } else {
            return set_prefix + '|' + set_index.toString();
        }
    }

    service.findIndex = function(array, key, value) {
        return array.reduce(function(acc, item, index) {
            if (item[key] == value) {
                acc = index;
            }
            return acc;
        }, null);
    }

    service.getSetLabel = function(questionset, set_prefix, set_index) {
        if (angular.isDefined(service.values[questionset.attribute]) &&
            angular.isDefined(service.values[questionset.attribute][set_prefix]) &&
            angular.isDefined(service.values[questionset.attribute][set_prefix][set_index]) &&
            angular.isDefined(service.values[questionset.attribute][set_prefix][set_index][0]) &&
            angular.isDefined(service.values[questionset.attribute][set_prefix][set_index][0].text)) {

            return service.values[questionset.attribute][set_prefix][set_index][0].text;
        } else {
            return '#' + (parseInt(set_index) + 1).toString();
        }
    }

    return service;

}]);
