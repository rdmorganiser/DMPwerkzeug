angular.module('project_questions')

.factory('QuestionsService', ['$http', '$timeout', '$location', '$rootScope', '$filter', '$q', '$window', '$sce', function($http, $timeout, $location, $rootScope, $filter, $q, $window, $sce) {

    service = {
        values: null
    };

    future = {};

    /* private varilables */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    var urls = {
        'projects': baseurl + 'api/projects/projects/',
        'values': baseurl + 'api/projects/values/',
        'catalog': baseurl + 'api/projects/catalogs/',
        'entities': baseurl + 'api/projects/entities/'
    };

    var back = false;

    /* private methods */

    function factory(ressource, parent) {
        if (ressource === 'values') {
            return {
                'text': '',
                'option': null,
                'snapshot': service.project.current_snapshot,
                'attribute': parent.attribute.id
            };

        } else if (ressource === 'valuesets') {
            return {
                'values': {},
            };
        }
    }

    /* public methods */

    service.init = function(project_id, summary_url) {
        service.summary_url = summary_url;

        $http.get(urls.projects + project_id + '/').success(function(response) {
            service.project = response;

            // get the question entity and the catalog (for the overview)
            $http.get(urls.catalog + service.project.catalog + '/').success(function(response) {
                future.catalog = response;

                service.initQuestionEntity($location.path().replace(/\//g,'')).then(function() {
                    service.catalog = angular.copy(future.catalog);

                    // enable back/forward button of browser
                    $rootScope.$on('$locationChangeSuccess', function (scope, next, current) {
                        var entity_id = parseInt($location.path().replace(/\//g,''), 10);
                        if (entity_id !== service.entity.id) {
                            service.initQuestionEntity(entity_id);
                        }
                    });
                });
            });
        });
    };

    service.initQuestionEntity = function(entity_id) {

        return service.fetchQuestionEntity(entity_id)
        .then(function() {
            return service.checkConditions();
        })
        .then(function() {
            return service.fetchValues();
        })
        .then(function () {
            // initialize values
            service.initValues();

            // copy entity
            service.entity = angular.copy(future.entity);

            // copy values
            if (service.entity.is_set) {
                // copy valuesets
                service.valuesets = angular.copy(future.valuesets);

                // activate fist valueset
                if (service.valuesets.length > 0) {
                    service.values = service.valuesets[0].values;
                } else {
                    service.values = null;
                }
            } else {
                // copy values
                service.values = angular.copy(future.values);
            }

            // focus the first field
            if (service.values) {
                var first_question = service.entity.questions[0];

                if (first_question.attribute.is_collection) {
                    service.focusField(first_question.attribute.id, 0);
                } else {
                    service.focusField(first_question.attribute.id);
                }
            }

            // set browser location, scroll to top and set back flag
            $location.path('/' + service.entity.id + '/');
            $window.scrollTo(0, 0);
            back = false;

        }, function () {
            // navigate to another question entity when checkConditions returned $q.reject
            if (back) {
                return service.initQuestionEntity(future.entity.prev);
            } else {
                return service.initQuestionEntity(future.entity.next);
            }
        });
    };

    service.initCheckbox = function(values, parent) {
        var checkbox_values = [];

        angular.forEach(parent.attribute.options, function(option) {
            var filter = $filter('filter')(values, function(value, index, array) {
                return value.option === option.id;
            });

            var value;
            if (filter.length === 1) {
                value = filter[0];
                value.removed = false;
            } else {
                value = factory('values', parent);
                value.removed = true;
                value.option = option.id;
            }

            checkbox_values.push(value);
        });

        return checkbox_values;
    };

    service.fetchQuestionEntity = function(entity_id) {
        var promise;

        // fetch the current (or the first) question entity from the server
        if (entity_id) {
            promise = $http.get(urls.entities + entity_id + '/');
        } else {
            promise = $http.get(urls.entities + 'first/', {
                params: {
                    catalog: service.project.catalog
                }
            });
        }

        // store the entity and return the promise
        return promise.then(function(result) {
            future.entity = result.data;

            // mark help text safe
            angular.forEach(future.entity.questions, function(question) {
                question.help = $sce.trustAsHtml(question.help);
            });
            if (future.entity.is_set) {
                future.entity.help = $sce.trustAsHtml(future.entity.help);
            }
        });
    };

    service.checkConditions = function() {
        if (future.entity.attribute_entity.conditions.length) {
            var promises = [];

            // fetch the values for these conditions from the server
            angular.forEach(future.entity.attribute_entity.conditions, function (condition) {
                var params = {
                    snapshot: service.project.current_snapshot,
                    attribute: condition.source_attribute
                };

                promises.push($http.get(urls.values, {'params': params}).success(function (response) {
                    condition.values = response;
                }));
            });

            return $q.all(promises).then(function(results) {

                var checks = [];
                angular.forEach(future.entity.attribute_entity.conditions, function (condition) {
                    angular.forEach(condition.values, function (value) {
                        checks.push(checkCondition(condition, value));
                    });
                });

                if (checks.length && checks.indexOf(true) === -1) {
                    return $q.reject();
                } else {
                    return $q.when();
                }
            });
        } else {
            return $q.when();
        }
    };

    service.fetchValues = function() {
        future.values = {};

        if (future.entity.is_set) {
            // init valuesets array
            future.valuesets = [];

            if (future.entity.collection) {

                // fetch all values for the parent_collection from the server
                return $http.get(urls.values, {
                    params: {
                        snapshot: service.project.current_snapshot,
                        attribute__parent_collection: future.entity.collection.id
                    }
                }).success(function(response) {

                    // loop over fetched values and sort them into valuesets
                    angular.forEach(response, function(value) {
                        // create a number of valuesets up to the one needed for this value
                        if (angular.isUndefined(future.valuesets[value.set_index])) {
                            while (future.valuesets.length < value.set_index + 1) {
                                future.valuesets.push(factory('valuesets'));
                            }
                        }

                        if (angular.isDefined(future.valuesets[value.set_index].values[value.attribute])) {
                            future.valuesets[value.set_index].values[value.attribute].push(value);
                        } else {
                            future.valuesets[value.set_index].values[value.attribute] = [value];
                        }
                    });
                });

            } else {
                // create he valueset
                future.valuesets.push(factory('valuesets'));

                // fetch all values for the attributes in this set from the server
                var promises = [];
                angular.forEach(future.entity.attributes, function(attribute_id) {
                    promises.push($http.get(urls.values, {
                        params: {
                            snapshot: service.project.current_snapshot,
                            attribute: attribute_id
                        }
                    }).success(function(response) {
                        angular.forEach(response, function(value) {
                            if (angular.isDefined(future.valuesets[0].values[value.attribute])) {
                                future.valuesets[0].values[value.attribute].push(value);
                            } else {
                                future.valuesets[0].values[value.attribute] = [value];
                            }
                        });
                    }));
                });

                return $q.all(promises);
            }

        } else {
            var question = future.entity.questions[0];

            return $http.get(urls.values, {
                params: {
                    snapshot: service.project.current_snapshot,
                    attribute: question.attribute.id
                }
            }).success(function(response) {
                future.values[question.attribute.id] = response;
            });
        }
    };

    service.initValues = function() {
        if (future.entity.is_set) {
            // loop over valuesets and questions to init values and widgets
            angular.forEach(future.valuesets, function(valueset) {
                angular.forEach(future.entity.questions, function(question) {

                    if (question.widget_type === 'checkbox') {
                        if (angular.isUndefined(valueset.values[question.attribute.id])) {
                            valueset.values[question.attribute.id] = [];
                        }
                        valueset.values[question.attribute.id] = service.initCheckbox(valueset.values[question.attribute.id],question);
                    } else {
                        if (angular.isUndefined(valueset.values[question.attribute.id])) {
                            valueset.values[question.attribute.id] = [factory('values', question)];
                        }
                    }

                    angular.forEach(valueset.values[question.attribute.id], function(value) {
                        service.initWidget(question, value);
                    });
                });
            });
        } else {
            var question = future.entity.questions[0];

            if (question.widget_type === 'checkbox') {
                future.values[question.attribute.id] = service.initCheckbox(future.values[question.attribute.id], question
                );
            } else {
                if (future.values[question.attribute.id].length < 1) {
                    future.values[question.attribute.id].push(factory('values', question));
                }
            }

            angular.forEach(future.values[question.attribute.id], function(value) {
                service.initWidget(question, value);
            });
        }
    };

    service.initWidget = function(question, value) {

        if (question.widget_type === 'radio') {
            value.input = {};

            angular.forEach(question.attribute.options, function(option) {
                if (option.additional_input) {
                    if (value.option === option.id) {
                        value.input[option.id] = value.text;
                    } else {
                        value.input[option.id] = '';
                    }
                }
            });
        }

        if (question.widget_type === 'range') {
            if (!value.text) {
                value.text = '0';
            }
        }

        if (question.widget_type === 'date') {
            $timeout(function() {
                $('.datepicker').datetimepicker({
                    format: 'YYYY-MM-DD'
                }).on('dp.change', function () {
                    $('.datepicker input').trigger('input');
                });
            });
        }
    };

    service.checkCondition = function(condition, value) {
        if (condition.relation === 'eq') {
            if (angular.isDefined(condition.target_option) && condition.target_option !== null) {
                return (condition.target_option == value.option);
            } else if (angular.isDefined(condition.target_text) && condition.target_text !== null) {
                return (condition.target_text == value.text);
            } else {
                return true;
            }
        } else if (condition.relation === 'neq') {
            if (angular.isDefined(condition.target_option) && condition.target_option !== null) {
                return (condition.target_option != value.option);
            } else if (angular.isDefined(condition.target_text) && condition.target_text !== null) {
                return (condition.target_text != value.text);
            } else {
                return true;
            }
        }
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

    service.getValueSetIndex = function() {
        var filter = $filter('filter')(service.valuesets, function(valueset, index, array) {
            valueset.index = index;
            return valueset.values == service.values;
        });

        if (angular.isDefined(filter[0])) {
            return filter[0].index;
        } else {
            return null;
        }
    };

    service.getPrevActiveValueSetIndex = function(index) {
        var prev_active_index = null;
        for (var i = index - 1; i >= 0; i--) {
            if (angular.isUndefined(service.valuesets[i].removed) || !service.valuesets[i].removed) {
                prev_active_index = i;
                break;
            }
        }
        return prev_active_index;
    };

    service.getNextActiveValueSetIndex = function(index) {
        var next_active_index = null;
        for (i = index + 1; i < service.valuesets.length; i++) {
            if (angular.isUndefined(service.valuesets[i].removed) || !service.valuesets[i].removed) {
                next_active_index = i;
                break;
            }
        }
        return next_active_index;
    };

    service.storeValue = function(value, collection_index, set_index) {
        var promise;

        if (value.removed) {
            // delete the value if it alredy exists on the server
            if (angular.isDefined(value.id)) {
                promise = $http.delete(urls.values + value.id + '/');
            }
        } else {
            // store the current index in the list
            value.set_index = set_index;
            value.collection_index = collection_index;

            if (angular.isDefined(value.id)) {
                // update an existing value
                promise = $http.put(urls.values + value.id + '/', value).success(function(response) {
                    angular.extend(value, response);
                });
            } else {
                // update a new value
                promise = $http.post(urls.values, value).success(function(response) {
                    angular.extend(value, response);
                });
            }
        }

        return promise;
    };

    service.storeValues = function() {
        var promises = [];

        if (service.entity.is_set) {

            var set_index = 0;
            angular.forEach(service.valuesets, function(valueset) {
                angular.forEach(service.entity.attributes, function(attribute_id) {
                    angular.forEach(valueset.values[attribute_id], function(value, collection_index) {
                        promises.push(service.storeValue(value, collection_index, set_index));
                    });
                });

                if (!valueset.removed) {
                    set_index++;
                }
            });
        } else {
            angular.forEach(service.entity.attributes, function(attribute_id) {
                angular.forEach(service.values[attribute_id], function(value, collection_index) {
                    promises.push(service.storeValue(value, collection_index, 0));
                });
            });
        }

        return $q.all(promises);
    };

    service.prev = function() {
        if (service.entity.prev !== null) {
            back = true;
            service.initQuestionEntity(service.entity.prev);
        }
    };

    service.next = function() {
        if (service.entity.next !== null) {
            service.initQuestionEntity(service.entity.next);
        }
    };

    service.jump = function(section, subsection, entity) {
        var next_entity_id = null;

        if (angular.isUndefined(subsection)) {
            next_entity_id = section.subsections[0].entities[0].id;
        } else if (angular.isUndefined(entity)) {
            next_entity_id = subsection.entities[0].id;
        } else {
            next_entity_id = entity.id;
        }

        if (next_entity_id) {
            service.initQuestionEntity(next_entity_id);
        }
    };

    service.save = function(proceed) {
        service.storeValues().then(function() {
            if (angular.isDefined(proceed) && proceed) {
                if (service.entity.is_set && service.entity.attribute_entity.is_collection) {
                    var index = service.getValueSetIndex();

                    var new_index = service.getNextActiveValueSetIndex(index);
                    if (new_index === null) {
                        if (service.entity.next === null) {
                            $window.location = service.summary_url;
                        } else {
                            service.next();
                        }
                    } else {
                        service.values = service.valuesets[new_index].values;
                        $window.scrollTo(0, 0);
                    }
                } else {
                    if (service.entity.next === null) {
                        $window.location = service.summary_url;
                    } else {
                        service.next();
                    }
                }
            }
        });
    };

    service.addValue = function(question) {
        var value = factory('values', question);

        //  add new value to service.values
        if (angular.isUndefined(service.values[question.attribute.id])) {
            service.values[question.attribute.id] = [value];
        } else {
            service.values[question.attribute.id].push(value);
        }

        service.initWidget(question, value);

        // focus the new value
        service.focusField(question.attribute.id, service.values[question.attribute.id].length - 1);
    };

    service.removeValue = function(attribute_id, index) {
        service.values[attribute_id][index].removed = true;
    };

    service.openValueSetModal = function(create) {

        service.modal_values = {};
        service.modal_errors = {};

        if (angular.isDefined(create) && create) {
            // set the create flag on the modal_values
            service.modal_values.create = true;
        } else {
            // get the existing title if there is a value for that
            if (service.entity.collection.id_attribute) {
                if (angular.isDefined(service.values[service.entity.collection.id_attribute.id])) {
                    service.modal_values = angular.copy(service.values[service.entity.collection.id_attribute.id][0]);
                }
            }
        }

        if (service.entity.collection.id_attribute) {
            $timeout(function() {
                $('#valuesets-form-modal').modal('show');
            });
        } else {
            service.submitValueSetModal();
        }
    };

    service.submitValueSetModal = function() {

        service.modal_errors = {};

        if (service.entity.collection.id_attribute) {
            if (angular.isUndefined(service.modal_values.text) || !service.modal_values.text) {
                service.modal_errors.text = [];
                return;
            }
        }

        // create a new valueset if the create flag was set
        if (angular.isDefined(service.modal_values.create) && service.modal_values.create) {
            service.addValueSet();
        }

        // create or update the value holding the id of the valuset
        if (service.entity.collection.id_attribute) {
            if (angular.isUndefined(service.values[service.entity.collection.id_attribute.id])) {
                service.values[service.entity.collection.id_attribute.id] = [{
                    'snapshot': service.project.current_snapshot,
                    'attribute': service.entity.collection.id_attribute.id,
                }];
            }

            service.values[service.entity.collection.id_attribute.id][0].text = service.modal_values.text;
        }

        $timeout(function() {
            $('#valuesets-form-modal').modal('hide');
        });
    };

    service.addValueSet = function() {
        // create a new valueset
        var valueset = factory('valuesets');

        // add values for the new valueset
        angular.forEach(service.entity.questions, function(question, index) {
            valueset.values[question.attribute.id] = [factory('values', question)];
        });

        // append the new valueset to the array of valuesets
        service.valuesets.push(valueset);

        // 'activate' the new valueset
        service.values = valueset.values;
    };

    service.removeValueSet = function() {
        // find current valueset
        var index = service.getValueSetIndex();

        // flag it for removal
        service.valuesets[index].removed = true;

        // flag all values as removed
        angular.forEach(service.entity.attributes, function(attribute_id) {
            angular.forEach(service.valuesets[index].values[attribute_id], function(value) {
                value.removed = true;
            });
        });

        // look for an non-removed valueset before the current one
        var new_index = service.getPrevActiveValueSetIndex(index);

        // if no was found, look  for an non-removed valueset after the current one
        if (new_index === null) {
            new_index = service.getNextActiveValueSetIndex(index);
        }

        // if there is still now new_index, set service.values to null, otherwise activate the valueset
        if (new_index === null) {
            service.values = null;
        } else {
            service.values = service.valuesets[new_index].values;
        }
    };

    return service;

}]);
