angular.module('catalogs', ['core'])

.config(['$locationProvider', function($locationProvider) {

    // set $location to not use #
    $locationProvider.html5Mode(true);

}])

.factory('CatalogsService', ['$resource', '$timeout', '$window', '$q', '$location', 'utils', function($resource, $timeout, $window, $q, $location, utils) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        catalogs: $resource(baseurl + 'api/v1/questions/catalogs/:list_action/:id/:detail_action/'),
        sections: $resource(baseurl + 'api/v1/questions/sections/:list_action/:id/:detail_action/'),
        questionsets: $resource(baseurl + 'api/v1/questions/questionsets/:list_action/:id/:detail_action/'),
        questions: $resource(baseurl + 'api/v1/questions/questions/:list_action/:id/:detail_action/'),
        attributes: $resource(baseurl + 'api/v1/domain/attributes/:list_action/:id/'),
        optionsets: $resource(baseurl + 'api/v1/options/optionsets/:list_action/:id/'),
        conditions: $resource(baseurl + 'api/v1/conditions/conditions/:list_action/:id/'),
        widgettypes: $resource(baseurl + 'api/v1/questions/widgettypes/'),
        valuetypes: $resource(baseurl + 'api/v1/questions/valuetypes/'),
        settings: $resource(baseurl + 'api/v1/core/settings/'),
        sites: $resource(baseurl + 'api/v1/core/sites/'),
        groups: $resource(baseurl + 'api/v1/core/groups/'),
    };

    /* configure factories */

    var factories = {
        catalogs: function(parent) {
            return {
                order: 0,
                sites: [1],
                uri_prefix: service.settings.default_uri_prefix,
                available: false
            };
        },
        sections: function(parent) {
            return {
                catalog: (angular.isDefined(parent) && parent) ? parent.id : null,
                order: 0,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        },
        questionsets: function(parent) {
            var section = null, questionset = null;
            if (angular.isDefined(parent) && parent) {
                if (parent.section) {
                    section = parent.section
                    questionset = parent.id;
                } else {
                    section = parent.id;
                }
            }
            return {
                section: section,
                questionset: questionset,
                attribute: null,
                order: 0,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        },
        questions: function(parent) {
            return {
                questionset: (angular.isDefined(parent) && parent) ? parent.id : null,
                attribute: null,
                order: 0,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix,
                default_option: null
            };
        }
    };

    /* create the questions service */

    var service = {};

    service.init = function() {
        service.widgettypes = resources.widgettypes.query();
        service.valuetypes = resources.valuetypes.query();
        service.settings = resources.settings.get();
        service.sites = resources.sites.query();
        service.groups = resources.groups.query();
        service.uri_prefixes = []
        service.uri_prefix = ''
        service.options = []
        service.filter = sessionStorage.getItem('questions_filter') || '';
        service.showQuestionSets = !(sessionStorage.getItem('options_showQuestionSets') === 'false');
        service.showQuestions = !(sessionStorage.getItem('options_showOptions') === 'false');

        resources.catalogs.query({list_action: 'index'}, function(response) {
            service.catalogs = response;

            // try to get the catalog from the address bar
            var catalog_id = $location.path().replace(/\//g,'');

            if (catalog_id) {
                service.current_catalog_id = catalog_id;
            } else if (service.catalogs.length) {
                service.current_catalog_id = service.catalogs[0].id;
            } else {
                service.current_catalog_id = null;
            }

            service.initView().then(function() {
                var current_scroll_pos = sessionStorage.getItem('questions_scroll_pos');
                if (current_scroll_pos) {
                    $timeout(function() {
                        $window.scrollTo(0, current_scroll_pos);
                    });
                }
            });
        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('questions_scroll_pos', $window.scrollY);
            sessionStorage.setItem('questions_filter', service.filter);
            sessionStorage.setItem('options_showQuestionSets', service.showQuestionSets);
            sessionStorage.setItem('options_showOptions', service.showQuestions);
        });
    };

    service.initView = function() {
        if (service.current_catalog_id) {
            $location.path('/' + service.current_catalog_id + '/');

            service.sections = resources.sections.query({list_action: 'index'});
            service.questionsets = resources.questionsets.query({list_action: 'index'});

            var catalog_promise = resources.catalogs.get({
                id: service.current_catalog_id,
                detail_action: 'nested'
            }, function(response) {
                service.catalog = response;
                service.uri_prefixes = [service.catalog.uri_prefix];

                // loop over all elements in the catalog to
                // (a) construct list of uri_prefixes
                // (b) sort questionsets and questions by order in one list called elements
                // using recursive functions!
                service.catalog.sections.map(service.initSection);

            }).$promise;

            return $q.all([
                service.sections.$promise,
                service.questionsets.$promise,
                catalog_promise
            ]);
        } else {
            $location.path('/');
            service.catalog = {};
            service.sections = [];
            service.questionsets = [];
            return $q.resolve();
        }
    };

    service.initSection = function(section) {
        if (service.uri_prefixes.indexOf(section.uri_prefix) < 0) {
            service.uri_prefixes.push(section.uri_prefix)
        }
        section.questionsets.map(service.initQuestionSet);
    };

    service.initQuestionSet = function(questionset) {
        if (service.uri_prefixes.indexOf(questionset.uri_prefix) < 0) {
            service.uri_prefixes.push(questionset.uri_prefix)
        }
        questionset.questionset = true;
        questionset.elements = questionset.questionsets.map(service.initQuestionSet)
                       .concat(questionset.questions.map(service.initQuestion))
                       .sort(function(a, b) {
                           return a.order - b.order;
                       });
        return questionset
    };

    service.initQuestion = function(question) {
        if (service.uri_prefixes.indexOf(question.uri_prefix) < 0) {
            service.uri_prefixes.push(question.uri_prefix)
        }
        question.question = true;
        return question
    };

    service.openFormModal = function(resource, obj, create, copy) {
        var promises = [];

        service.errors = {};
        service.values = utils.fetchValues(resources[resource], factories[resource], obj, create, copy);
        promises.push(service.values.$promise);

        if (resource === 'questionsets' || resource === 'questions') {
            service.attributes = resources.attributes.query({list_action: 'index'});
            promises.push(service.attributes.$promise);

            service.conditions = resources.conditions.query({list_action: 'index'});
            promises.push(service.conditions.$promise);
        }

        if (resource === 'questions') {
            service.optionsets = resources.optionsets.query({list_action: 'index'});
            promises.push(service.optionsets.$promise);
        }

        $q.all(promises).then(function() {
            service.updateOptions();
            $('#' + resource + '-form-modal').modal('show');
            $timeout(function() {
                $('formgroup[data-quicksearch="true"]').trigger('refresh');
            });
        });
    };

    service.submitFormModal = function(resource) {
        utils.storeValues(resources[resource], service.values).then(function(response) {
            if (resource === 'catalogs') {
                resources.catalogs.query({list_action: 'index'}, function(catalogs) {
                    service.catalogs = catalogs;
                    service.current_catalog_id = response.id;
                    service.initView();
                });
            } else {
                service.initView();
            }

            $('#' + resource + '-form-modal').modal('hide');
        }, function(result) {
            service.errors = result.data;
        });
    };

    service.openDeleteModal = function(resource, obj) {
        service.values = obj;
        $('#' + resource + '-delete-modal').modal('show');
    };

    service.submitDeleteModal = function(resource) {
        resources[resource].delete({id: service.values.id}, function() {
            if (resource === 'catalogs') {
                resources.catalogs.query({list_action: 'index'}, function(catalogs) {
                    service.catalogs = catalogs;

                    if (service.catalogs.length) {
                        service.current_catalog_id = service.catalogs[0].id;
                    } else {
                        service.current_catalog_id = null;
                    }

                    service.initView();
                });
            } else {
                service.initView();
            }

            $('#' + resource + '-delete-modal').modal('hide');
        });
    };

    service.hideCatalog = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.title.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    service.hideSection = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.title.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    service.hideQuestionSet = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.title.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    service.hideQuestion = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.text.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    service.updateOptions = function() {
        if (angular.isDefined(service.optionsets) && angular.isDefined(service.values.optionsets))
        service.options = service.optionsets.reduce(function (options, optionset) {
            if (service.values.optionsets.indexOf(optionset.id) > -1) {
                options = options.concat(optionset.options);
            }
            return options;
        }, []);
    }

    return service;

}])

.controller('CatalogsController', ['$scope', 'CatalogsService', function($scope, CatalogsService) {

    $scope.service = CatalogsService;
    $scope.service.init();

    // watch service.values.optionsets to recompute service.options
    $scope.$watch(function() {
        // to be evaluated each $digest cycle
        if (angular.isDefined($scope.service.values)) {
            return $scope.service.values.optionsets;
        }
    }, function(newValue, oldValue) {
        if (angular.isDefined(newValue)) {
            $scope.service.updateOptions();
        }
    });

}]);
