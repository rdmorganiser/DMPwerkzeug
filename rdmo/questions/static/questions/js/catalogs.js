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
            return {
                section: (angular.isDefined(parent) && parent) ? parent.id : null,
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
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        }
    };

    /* create the questions service */

    var service = {};

    service.init = function() {
        service.attributes = resources.attributes.query({list_action: 'index'});
        service.optionsets = resources.optionsets.query({list_action: 'index'});
        service.conditions = resources.conditions.query({list_action: 'index'});
        service.widgettypes = resources.widgettypes.query();
        service.valuetypes = resources.valuetypes.query();
        service.settings = resources.settings.get();
        service.sites = resources.sites.query();
        service.groups = resources.groups.query();
        service.uri_prefixes = []
        service.uri_prefix = ''

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
                var current_scroll_pos = sessionStorage.getItem('current_scroll_pos');
                if (current_scroll_pos) {
                    $timeout(function() {
                        $window.scrollTo(0, current_scroll_pos);
                    });
                }
            });

        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('current_scroll_pos', $window.scrollY);
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

                // construct list of uri_prefixes
                service.uri_prefixes = [service.catalog.uri_prefix]
                service.catalog.sections.map(function(section) {
                    if (service.uri_prefixes.indexOf(section.uri_prefix) < 0) {
                        service.uri_prefixes.push(section.uri_prefix)
                    }
                    section.questionsets.map(function(questionset) {
                        if (service.uri_prefixes.indexOf(questionset.uri_prefix) < 0) {
                            service.uri_prefixes.push(questionset.uri_prefix)
                        }
                        questionset.questions.map(function(question) {
                            if (service.uri_prefixes.indexOf(question.uri_prefix) < 0) {
                                service.uri_prefixes.push(question.uri_prefix)
                            }
                        });
                    });
                });
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

    service.openFormModal = function(resource, obj, create, copy) {
        service.errors = {};
        service.values = utils.fetchValues(resources[resource], factories[resource], obj, create, copy);

        $q.when(service.values.$promise).then(function() {
            $('#' + resource + '-form-modal').modal('show');
            $('formgroup[data-quicksearch="true"]').trigger('refresh');
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
        var hide = false;

        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.title.indexOf(service.filter) < 0) {
            hide = true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            hide = true;
        }

        if (hide === true) {
            // hide only if all questions of this questionset are hidden
            return item.questions.every(function(question) {
                return service.hideQuestion(question) === true;
            });
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

    return service;

}])

.controller('CatalogsController', ['$scope', 'CatalogsService', function($scope, CatalogsService) {

    $scope.service = CatalogsService;
    $scope.service.init();
}]);
