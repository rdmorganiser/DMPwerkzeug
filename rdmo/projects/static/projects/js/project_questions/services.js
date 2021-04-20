angular.module('project_questions')

.factory('QuestionsService', ['$resource', '$http', '$timeout', '$location', '$rootScope', '$filter', '$q', '$window', '$sce', function($resource, $http, $timeout, $location, $rootScope, $filter, $q, $window, $sce) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        projects: $resource(baseurl + 'api/v1/projects/projects/:id/:detail_action/'),
        values: $resource(baseurl + 'api/v1/projects/projects/:project/values/:id/'),
        questionsets: $resource(baseurl + 'api/v1/projects/projects/:project/questionsets/:list_action/:id/')
    };

    /* configure factories */

    var factories = {
        values: function(question) {
            var text = '';
            if (['text', 'textarea', 'yesno', 'range', 'date'].indexOf(question.widget_type) > -1) {
                text = question.default_text;
            }
            return {
                text: text,
                option: null,
                file: null,
                selected: null,
                project: service.project.id,
                attribute: question.attribute.id
            };
        },
        valuesets: function() {
            return {
                values: {}
            };
        }
    };

    /* create a buffer for the future service content */

    var future = {};

    /* create a flag to be used when clicking the prev button */

    var back = false;

    /* create a flag to be used when the view is initializing */

    var initializing = false;

    /* create the questions service */

    var service = {
        values: null
    };

    service.init = function(project_id) {
        resources.projects.get({id: project_id, detail_action: 'overview'}, function(response) {
            service.project = response;

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
        });
    };

    service.initView = function(questionset_id) {

        if (initializing) return;

        if (questionset_id !== null) {

            // enable initializing flag
            initializing = true;

            return service.fetchQuestionSet(questionset_id)
            .then(function() {
                return service.checkConditions();
            })
            .then(function() {
                return service.initOptions();
            })
            .then(function() {
                return service.checkOptionSetConditions();
            })
            .then(function() {
                return service.fetchValues();
            })
            .then(function () {
                // initialize values
                service.initValues();

                // copy questionset
                service.questionset = angular.copy(future.questionset);

                // copy progress
                service.progress = angular.copy(future.progress);

                // copy valuesets
                service.valueset_list = angular.copy(future.valueset_list);
                service.valuesets = angular.copy(future.valuesets);

                // activate fist valueset
                if (service.valueset_list.length) {
                    service.activateValueSet(service.valueset_list[0])
                } else {
                    service.activateValueSet(null);
                }

                // focus the first field
                if (service.values && Object.keys(service.values).length) {
                    var first_question = service.questionset.questions[0];

                    if (first_question.widget_type != 'date') {
                        if (first_question.is_collection) {
                            service.focusField(first_question.attribute.id, 0);
                        } else {
                            service.focusField(first_question.attribute.id);
                        }
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
                if (result === false) {
                    // checkConditions returned $q.reject

                    // disable initializing flag again
                    initializing = false;

                    // navigate to another question questionset when checkConditions returned $q.reject
                    if (back) {
                        return service.initView(future.questionset.prev);
                    } else {
                        return service.initView(future.questionset.next);
                    }
                }
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
            // mark the help text of the question set 'save'
            future.questionset.help = $sce.trustAsHtml(future.questionset.help);

            // mark help text safe
            angular.forEach(future.questionset.questions, function(question) {
                // mark the help text of the question 'save'
                question.help = $sce.trustAsHtml(question.help);
            });
        });
    };

    service.checkConditions = function() {
        if (future.questionset.conditions && future.questionset.conditions.length) {
            var results = [],
                promises = [];

            // fetch the values for these conditions from the server
            angular.forEach(future.questionset.conditions, function (condition) {
                promises.push(resources.projects.get({
                    detail_action: 'resolve',
                    condition: condition.id,
                    id: service.project.id,
                }, function(response) {
                    results.push(response.result);
                }).$promise);
            });

            return $q.all(promises).then(function() {
                if (results.length && results.indexOf(true) === -1) {
                    return $q.reject(false);
                } else {
                    return $q.when();
                }
            });
        } else {
            return $q.when();
        }
    };

    service.initOptions = function() {
        promises = [];

        angular.forEach(future.questionset.questions, function(question) {
            if (question.optionsets.length) {
                // init options array for this questions attribute
                question.options = [];

                angular.forEach(question.optionsets, function(optionset) {
                    if (optionset.provider) {
                        // call the provider to get addtional options
                        promises.push(resources.projects.query({
                            detail_action: 'options',
                            optionset: optionset.id,
                            id: service.project.id,
                        }, function(response) {
                            question.options = question.options.concat(response.map(function(option) {
                                option.additional_input = false  // additional input is never allowed for provider optionsets
                                option.provider = optionset.provider
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

    service.checkOptionSetConditions = function() {
        promises = [];

        angular.forEach(future.questionset.questions, function(question) {
            if (question.optionsets.length) {
                angular.forEach(question.optionsets, function(optionset) {
                    // check for the condition of the optionset
                    if (optionset.conditions.length) {
                        // set all options of this optionset to hidden
                        angular.forEach(optionset.options, function(option) {
                            option.hidden = true;
                        });

                        angular.forEach(optionset.conditions, function (condition_id) {
                            promises.push(resources.projects.get({
                                detail_action: 'resolve',
                                condition: condition_id,
                                id: service.project.id,
                            }, function(response) {
                                if (response.result) {
                                    // un-hide all options
                                    angular.forEach(optionset.options, function(option) {
                                        option.hidden = false;
                                    });
                                }
                            }).$promise);
                        });
                    }
                });
            }
        });

        return $q.all(promises);
    };

    service.fetchValues = function() {
        future.values = {};

        // init valuesets array
        future.valueset_list = [];
        future.valuesets = {};

        var promises = [];

        // fetch current progress for this project
        promises.push(resources.projects.get({
            id: service.project.id,
            detail_action: 'progress'
        }, function(response) {
            future.progress = response;
        }).$promise);

        if (future.questionset.is_collection) {
            // fetch all values for the set from the server
            promises.push(resources.values.query({
                project: service.project.id,
                set_attribute: future.questionset.attribute.id
            }, function(response) {
                // important: the values in response need to be ordered by set_index and collection_index
                // loop over fetched values and sort them into valuesets
                angular.forEach(response, function(value) {
                    if (angular.isUndefined(future.valuesets[value.set_index])) {
                        future.valuesets[value.set_index] = factories.valuesets();
                        future.valueset_list.push(value.set_index);
                    }

                    if (angular.isDefined(future.valuesets[value.set_index].values[value.attribute])) {
                        future.valuesets[value.set_index].values[value.attribute].push(value);
                    } else {
                        future.valuesets[value.set_index].values[value.attribute] = [value];
                    }
                });
            }).$promise);

        } else {
            // create the (only) valueset
            future.valueset_list = [0];
            future.valuesets[0] = factories.valuesets();

            // fetch all values for the attributes in this set from the server
            angular.forEach(future.questionset.questions, function(question) {
                var attribute_id = question.attribute.id;

                promises.push(resources.values.query({
                    project: service.project.id,
                    attribute: attribute_id
                }, function(response) {
                    angular.forEach(response, function(value) {
                        if (angular.isDefined(future.valuesets[0].values[value.attribute])) {
                            future.valuesets[0].values[value.attribute].push(value);
                        } else {
                            future.valuesets[0].values[value.attribute] = [value];
                        }
                    });
                }).$promise);
            });
        }

        return $q.all(promises);
    };

    service.initValues = function() {
        // loop over valuesets and questions to init values and widgets
        angular.forEach(future.valuesets, function(valueset) {
            angular.forEach(future.questionset.questions, function(question) {
                var attribute_id = question.attribute.id;

                if (question.widget_type === 'checkbox') {
                    if (angular.isUndefined(valueset.values[attribute_id])) {
                        valueset.values[attribute_id] = [];
                    }
                    valueset.values[attribute_id] = service.initCheckbox(valueset.values[attribute_id], question);
                } else {
                    if (angular.isUndefined(valueset.values[attribute_id])) {
                        valueset.values[attribute_id] = [factories.values(question)];
                    }
                }

                angular.forEach(valueset.values[attribute_id], function(value) {
                    service.initSelected(question, value);
                    service.initWidget(question, value);
                });
            });
        });
    };

    service.initSelected = function(question, value) {
        // get the index of the selected option to be used in radio and select widgets
        value.selected = null;
        angular.forEach(question.options, function(option, index) {
            option.index = index;

            if (option.provider && option.external_id == value.external_id) {
                value.selected = index
            } else if (value.option && option.id == value.option) {
                value.selected = index
            }
        })
    }

    service.initWidget = function(question, value) {
        if (question.widget_type === 'radio') {
            value.additional_input = {};

            angular.forEach(question.options, function(option, index) {
                if (option.additional_input) {
                    if (value.selected === index) {
                        value.additional_input[index] = value.text;
                    } else {
                        value.additional_input[index] = '';
                    }
                }
            });
        }

        if (question.widget_type === 'range') {
            if (!value.text) {
                value.text = '0';
            }
        }

        if (question.widget_type === 'autocomplete') {
            if (value.option) {
                value.locked = true;
            }
        }
    };

    service.initCheckbox = function(values, question) {
        var checkbox_values = [];

        angular.forEach(question.options, function(option) {
            var filter = $filter('filter')(values, function(value, index, array) {
                if (option.provider && option.external_id == value.external_id) {
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

                if (option.provider) {
                    value.external_id = option.external_id;
                } else {
                    value.option = option.id;
                }
            }

            checkbox_values.push(value);
        });

        return checkbox_values;
    };

    service.focusField = function(attribute_id, index) {
        $timeout(function() {
            if (angular.isDefined(index)) {
                angular.element('#id_' + attribute_id.toString() + '_' + index.toString()).focus();
            } else {
                angular.element('#id_' + attribute_id.toString()).focus();
            }
        });
    };

    service.storeValue = function(value, question, collection_index, set_index) {

        if (angular.isDefined(value.removed) && value.removed) {
            // delete the value if it alredy exists on the server
            if (angular.isDefined(value.id)) {
                return resources.values.delete({
                    id: value.id,
                    project: service.project.id
                }).$promise;
            }
        } else {
            // store the current index in the list
            value.set_index = set_index;
            value.collection_index = collection_index;

            if (question === null) {
                // this is the id of a new valueset
                value.value_type = 'text';
                value.unit = '';
            } else {
                value.value_type = question.value_type;
                value.unit = question.unit;
            }

            // filter options for the selected id
            if (angular.isDefined(value.selected) && value.selected !== null) {
                var option = question.options[value.selected]

                if (option.provider) {
                    value.text = option.text;
                    value.option = null;
                    value.external_id = option.external_id;
                } else {
                    value.option = option.id;
                    value.external_id = '';
                }
            } else {
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
                    }).error(function (response) {
                        value.errors = response.value;
                    });
                } else {
                    angular.extend(value, response);
                }
            }, function (response) {
                value.errors = response.data.value;
            })
        }
    };

    service.storeValues = function() {
        var promises = [];

        angular.forEach(service.valueset_list, function(set_index) {
            angular.forEach(service.questionset.questions, function(question) {
                var attribute_id = question.attribute.id;
                var values = service.valuesets[set_index].values[attribute_id];

                angular.forEach(values, function(value, collection_index) {
                    promises.push(service.storeValue(value, question, collection_index, set_index));
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
        var next_questionset_id = null;

        if (angular.isUndefined(questionset)) {
            next_questionset_id = section.questionsets[0].id;
        } else {
            next_questionset_id = questionset.id;
        }

        if (next_questionset_id) {
            service.initView(next_questionset_id);
        }
    };

    service.save = function(proceed) {
        service.storeValues().then(function() {
            if (angular.isDefined(proceed) && proceed) {
                if (service.questionset.is_collection) {
                    if (service.valueset_list.length) {
                        // get the index of the current set_index in service.values_list
                        var index = service.valueset_list.indexOf(service.valueset_index);

                        if (index == service.valueset_list.length - 1) {
                            // it the last valueset, go to the next page
                            service.next();
                        } else {
                            // activate the next valueset
                            service.activateValueSet(service.valueset_list[index + 1]);
                            $window.scrollTo(0, 0);
                        }
                    } else {
                        service.next();
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
                })
            }
        });
    };

    service.addValue = function(question) {
        var value = factories.values(question);

        //  add new value to service.values
        if (angular.isUndefined(service.values[question.attribute.id])) {
            service.values[question.attribute.id] = [value];
        } else {
            service.values[question.attribute.id].push(value);
        }

        service.initSelected(question, value);
        service.initWidget(question, value);

        // focus the new value
        service.focusField(question.attribute.id, service.values[question.attribute.id].length - 1);
    };

    service.eraseValue = function(attribute_id, index) {
        service.values[attribute_id][index].text = '';
        service.values[attribute_id][index].additional_input = {};
        service.values[attribute_id][index].file_url = null;
        service.values[attribute_id][index].file = false;
        service.values[attribute_id][index].selected = null;
    };

    service.removeValue = function(attribute_id, index) {
        service.values[attribute_id][index].removed = true;
    };

    service.openValueSetFormModal = function(create) {

        service.modal_values = {};
        service.modal_errors = {};

        if (angular.isDefined(create) && create) {
            // set the create flag on the modal_values
            service.modal_values.create = true;
        } else {
            // get the existing title if there is a value for that
            if (service.questionset.attribute.id_attribute) {
                if (angular.isDefined(service.values[service.questionset.attribute.id_attribute.id])) {
                    service.modal_values = angular.copy(service.values[service.questionset.attribute.id_attribute.id][0]);
                }
            }
        }

        if (service.questionset.attribute.id_attribute) {
            $timeout(function() {
                $('#valuesets-form-modal').modal('show');
            });
        } else {
            service.addValueSet();
        }
    };

    service.submitValueSetFormModal = function() {
        service.modal_errors = {};

        // va;idate that there is any title given
        if (service.questionset.attribute.id_attribute) {
            if (angular.isUndefined(service.modal_values.text) || !service.modal_values.text) {
                service.modal_errors.text = [];
                return;
            }
        }

        // create a new valueset if the create flag was set
        if (angular.isDefined(service.modal_values.create) && service.modal_values.create) {
            service.addValueSet(service.modal_values.text);
        } else {
            service.updateValueSet(service.modal_values.text);
        }

        $timeout(function() {
            $('#valuesets-form-modal').modal('hide');
        });
    };

    service.openValueSetDeleteModal = function() {
        $timeout(function() {
            $('#valuesets-delete-modal').modal('show');
        });
    };

    service.submitValueSetDeleteModal = function() {
        service.removeValueSet();
        $timeout(function() {
            $('#valuesets-delete-modal').modal('hide');
        });
    };

    service.addValueSet = function(text) {
        // get the last set_index and create the new one
        var set_index;
        if (service.valueset_list.length) {
            set_index = service.valueset_list[service.valueset_list.length - 1] + 1;
        } else {
            set_index = 0
        }

        // create a new valueset
        var valueset = factories.valuesets();

        // loop over questions similar to initView
        angular.forEach(service.questionset.questions, function(question) {
            var attribute_id = question.attribute.id;

            if (question.widget_type === 'checkbox') {
                if (angular.isUndefined(valueset.values[attribute_id])) {
                    valueset.values[attribute_id] = [];
                }
                valueset.values[attribute_id] = service.initCheckbox(valueset.values[attribute_id], question);
            } else {
                if (angular.isUndefined(valueset.values[attribute_id])) {
                    valueset.values[attribute_id] = [factories.values(question)];
                }
            }

            angular.forEach(valueset.values[attribute_id], function(value) {
                service.initSelected(question, value);
                service.initWidget(question, value);
            });
        });

        if (service.questionset.attribute.id_attribute) {
            var id_attribute_id = service.questionset.attribute.id_attribute.id;

            // create a value to hold the id of the valuset
            var value = {
                'project': service.project.id,
                'attribute': id_attribute_id,
                'text': text
            };

            valueset.values[id_attribute_id] = [value];
            service.storeValue(value, null, 0, set_index);
        }

        // append the new valueset to the array of valuesets
        service.valueset_list.push(set_index);
        service.valuesets[set_index] = valueset;

        // 'activate' the new valueset
        service.activateValueSet(set_index);
    };

    service.updateValueSet = function(text) {
        // get the current set_index
        var set_index = service.valueset_index;

        // get the id of the id_attribute of the questionset
        var id_attribute_id = service.questionset.attribute.id_attribute.id;

        // create a value to hold the id of the valuset if it does not exist yet
        if (angular.isUndefined(service.values[id_attribute_id])) {
            service.values[id_attribute_id] = [{
                'project': service.project.id,
                'attribute': id_attribute_id
            }];
        }

        // update the value holding the id of the valuset
        var value = service.values[service.questionset.attribute.id_attribute.id][0];
        value.text = text;

        // store the value on the server
        service.storeValue(value, null, 0, set_index);
    };

    service.removeValueSet = function() {
        // get the current set_index
        var set_index = service.valueset_index;

        // get the index in service.values_list
        var index = service.valueset_list.indexOf(set_index);

        // delete values on the server
        angular.forEach(service.values, function(values) {
            angular.forEach(values, function(value) {
                value.removed = true;
                service.storeValue(value, null, value.collection_index, set_index);
            });
        });

        // activate the valueset before the current one
        if (service.valueset_list.length == 1) {
            service.activateValueSet(null);
        } else if (index == 0) {
            service.activateValueSet(service.valueset_list[1]);
        } else {
            service.activateValueSet(service.valueset_list[index - 1]);
        }

        // delete the valueset
        service.valueset_list.splice(index, 1);
        delete service.valuesets[set_index];
    };

    service.activateValueSet = function(set_index) {
        if (set_index === null) {
            service.valueset_index = null;
            service.values = null;
        } else {
            service.valueset_index = set_index;
            service.values = service.valuesets[set_index].values;
        }
    };

    service.filterAutocomplete = function(question, value) {
        value.items = $filter('filter')(question.options, {text: value.autocomplete});
    };

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
                    value.autocomplete = next.text;
                }
            } else if ($event.code == 'Enter' || $event.code == 'NumpadEnter') {
                if (angular.isDefined(active)) {
                    service.selectAutocomplete(value, value.items[active]);
                }
            } else if ($event.code == 'Escape') {
                if (value.selected === null) {
                    value.autocomplete = '';
                    service.filterAutocomplete(question, value.items[active]);
                } else {
                    value.locked = true;
                }
            }
        }
    };

    service.selectAutocomplete = function(value, option) {
        value.locked = true;
        value.selected = option.index;
    }

    service.blurAutocomplete = function(value) {
        if (value.selected === null) {
            value.autocomplete = '';
            value.items = null;
        } else {
            value.locked = true;
        }
    }

    service.unlockAutocomplete = function(question, value, index) {
        if (value.selected === null) {
            value.autocomplete = '';
        } else {
            value.autocomplete = question.options[value.selected].text;
        }
        value.locked = false;
        service.focusField(question.attribute.id, index);
    };

    service.isDefaultValue = function(question, value) {
        return !value.id && question.default_text && (question.default_text == value.text)
    }

    return service;

}]);
