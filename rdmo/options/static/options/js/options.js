angular.module('options', ['core'])

.factory('OptionsService', ['$resource', '$timeout', '$window', '$q', 'utils', function($resource, $timeout, $window, $q, utils) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        optionsets: $resource(baseurl + 'api/v1/options/optionsets/:list_action/:id/:detail_action/'),
        options: $resource(baseurl + 'api/v1/options/options/:list_action/:id/:detail_action/'),
        conditions: $resource(baseurl + 'api/v1/conditions/conditions/:list_action/:id/'),
        providers: $resource(baseurl + 'api/v1/options/providers/:id/'),
        settings: $resource(baseurl + 'api/v1/core/settings/'),
    };

    /* configure factories */

    var factories = {
        optionsets: function() {
            return {
                order: 0,
                uri_prefix: service.settings.default_uri_prefix
            };
        },
        options: function(parent) {
            return {
                order: 0,
                optionset: (angular.isDefined(parent) && parent) ? parent.id : null,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        }
    };

    /* create the options service */

    var service = {};

    service.init = function(options) {
        service.providers = resources.providers.query();
        service.settings = resources.settings.get();
        service.uri_prefixes = [];
        service.uri_prefix = '';
        service.filter = sessionStorage.getItem('options_filter') || '';
        service.showOptions = !(sessionStorage.getItem('options_showOptions') === 'false');

        service.initView().then(function () {
            var current_scroll_pos = sessionStorage.getItem('options_scroll_pos');
            if (current_scroll_pos) {
                $timeout(function() {
                    $window.scrollTo(0, current_scroll_pos);
                });
            }
        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('options_scroll_pos', $window.scrollY);
            sessionStorage.setItem('options_filter', service.filter);
            sessionStorage.setItem('options_showOptions', service.showOptions);
        });
    };

    service.initView = function(options) {
        return resources.optionsets.query({list_action: 'nested'}, function(response) {
            service.optionsets = response;

            // construct list of uri_prefixes
            service.uri_prefixes = []
            service.optionsets.map(function(optionset) {
                if (service.uri_prefixes.indexOf(optionset.uri_prefix) < 0) {
                    service.uri_prefixes.push(optionset.uri_prefix)
                }
                optionset.options.map(function(option) {
                    if (service.uri_prefixes.indexOf(option.uri_prefix) < 0) {
                        service.uri_prefixes.push(option.uri_prefix)
                    }
                });
            });
        }).$promise;
    };

    service.openFormModal = function(resource, obj, create, copy) {
        var fetch_resource = (resource === 'conditions') ? 'optionsets': resource;

        service.errors = {};
        service.values = utils.fetchValues(resources[fetch_resource], factories[resource], obj, create, copy);
        service.conditions = resources.conditions.query({list_action: 'index'});

        $q.when([
            service.values.$promise,
            service.conditions.$promise
        ]).then(function() {
            $('#' + resource + '-form-modal').modal('show');
            $timeout(function() {
                $('formgroup[data-quicksearch="true"]').trigger('refresh');
            });
        });
    };

    service.submitFormModal = function(resource) {
        var submit_resource = (resource === 'conditions') ? 'optionsets': resource;

        utils.storeValues(resources[submit_resource], service.values).then(function() {
            $('#' + resource + '-form-modal').modal('hide');
            service.initView();
        }, function(result) {
            service.errors = result.data;
        });
    };

    service.openDeleteModal = function(resource, obj) {
        utils.fetchValues(resources[resource], factories[resource], obj).$promise.then(function(response) {
            service.values = response;
            service.values.options = obj.options;
            $('#' + resource + '-delete-modal').modal('show');
        });
    };

    service.submitDeleteModal = function(resource) {
        resources[resource].delete({id: service.values.id}, function() {
            $('#' + resource + '-delete-modal').modal('hide');
            service.initView();
        });
    };

    service.openShowModal = function(resource, obj) {
        service.values = utils.fetchValues(resources[resource], factories[resource], obj)

        $q.when(service.values.$promise).then(function() {
            $('#' + resource + '-show-modal').modal('show');
        });
    };

    service.hideOptionSet = function(item) {
        var hide = false;

        if (service.filter && item.key.indexOf(service.filter) < 0) {
            hide = true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            hide = true;
        }

        if (hide === true) {
            // hide only if all options of this optionsset are hidden
            return item.options.every(function(option) {
                return service.hideOption(option) === true;
            });
        }
    };

    service.hideOption = function(item) {
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

.controller('OptionsController', ['$scope', 'OptionsService', function($scope, OptionsService) {

    $scope.service = OptionsService;
    $scope.service.init();

}]);
