angular.module('conditions', ['core'])

.factory('ConditionsService', ['$resource', '$timeout', '$window', '$q', '$filter', 'utils', function($resource, $timeout, $window, $q, $filter, utils) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        conditions: $resource(baseurl + 'api/v1/conditions/conditions/:list_action/:id/:detail_action/'),
        relations: $resource(baseurl + 'api/v1/conditions/relations/:id/'),
        attributes: $resource(baseurl + 'api/v1/domain/attributes/:id/'),
        options: $resource(baseurl + 'api/v1/options/options/:id/'),
        settings: $resource(baseurl + 'api/v1/core/settings/'),
    };

    /* configure factories */

    var factories = {
        conditions: function(parent) {
            return {
                source: null,
                relation: null,
                target_option: null,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        }
    };

    /* create the conditions service */

    var service = {};

    service.init = function(options) {
        service.relations = resources.relations.query();
        service.settings = resources.settings.get();
        service.uri_prefixes = []
        service.uri_prefix = ''
        service.filter = sessionStorage.getItem('conditions_filter') || '';

        service.initView().then(function () {
            var current_scroll_pos = sessionStorage.getItem('conditions_scroll_pos');
            if (current_scroll_pos) {
                $timeout(function() {
                    $window.scrollTo(0, current_scroll_pos);
                });
            }
        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('conditions_scroll_pos', $window.scrollY);
            sessionStorage.setItem('conditions_filter', service.filter);
        });
    };

    service.initView = function(options) {
        return resources.conditions.query({list_action: 'index'}, function(response) {
            service.conditions = response;
            service.uri_prefixes = response.reduce(function(list, item) {
                if (list.indexOf(item.uri_prefix) < 0) {
                    list.push(item.uri_prefix)
                }
                return list
            }, [])
        }).$promise;
    };

    service.openFormModal = function(resource, obj, create, copy) {
        service.errors = {};
        service.values = utils.fetchValues(resources[resource], factories[resource], obj, create, copy);
        service.attributes = resources.attributes.query();
        service.options = resources.options.query();

        $q.all([
            service.values.$promise,
            service.attributes.$promise,
            service.options.$promise
        ]).then(function() {
            $('#' + resource + '-form-modal').modal('show');
            $timeout(function() {
                $('formgroup[data-quicksearch="true"]').trigger('refresh');
            });
        });
    };

    service.submitFormModal = function(resource) {
        utils.storeValues(resources[resource], service.values).then(function() {
            $('#' + resource + '-form-modal').modal('hide');
            service.initView();
        }, function(result) {
            service.errors = result.data;
        });
    };

    service.openDeleteModal = function(resource, obj) {
        utils.fetchValues(resources[resource], factories[resource], obj).$promise.then(function(response) {
            service.values = response;
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

    service.hideCondition = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    return service;

}])

.controller('ConditionsController', ['$scope', 'ConditionsService', function($scope, ConditionsService) {

    $scope.service = ConditionsService;
    $scope.service.init();

}]);
