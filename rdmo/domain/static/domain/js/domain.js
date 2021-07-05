angular.module('domain', ['core'])

.factory('DomainService', ['$resource', '$timeout', '$window', '$q', 'utils', function($resource, $timeout, $window, $q, utils) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        attributes: $resource(baseurl + 'api/v1/domain/attributes/:list_action/:id/:detail_action/'),
        settings: $resource(baseurl + 'api/v1/core/settings/'),
    };

    /* configure factories */

    var factories = {
        attributes: function(parent) {
            return {
                parent: (angular.isDefined(parent) && parent) ? parent.id : null,
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix
            };
        }
    };

    /* create the domain service */

    var service = {};

    service.init = function(options) {
        service.settings = resources.settings.get();
        service.uri_prefixes = []
        service.uri_prefix = ''
        service.filter = sessionStorage.getItem('domain_filter') || '';

        service.initView().then(function () {
            var current_scroll_pos = sessionStorage.getItem('domain_scroll_pos');
            if (current_scroll_pos) {
                $timeout(function() {
                    $window.scrollTo(0, current_scroll_pos);
                });
            }
        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('domain_scroll_pos', $window.scrollY);
            sessionStorage.setItem('domain_filter', service.filter);
        });
    };

    service.initView = function() {
        service.domain = resources.attributes.query({list_action: 'nested'})
        service.attributes = resources.attributes.query(function(response) {
            service.uri_prefixes = response.reduce(function(list, item) {
                if (list.indexOf(item.uri_prefix) < 0) {
                    list.push(item.uri_prefix)
                }
                return list
            }, [])
        });

        return $q.all([
            service.domain.$promise,
            service.attributes.$promise
        ]);
    };

    service.openFormModal = function(resource, obj, create, copy) {
        service.errors = {};
        service.values = utils.fetchValues(resources[resource], factories[resource], obj, create, copy);

        $q.when(service.values.$promise).then(function() {
            $('#' + resource + '-form-modal').modal('show');
            $timeout(function() {
                $('formgroup[data-quicksearch="true"]').trigger('refresh');
            });
        });
    };

    service.submitFormModal = function(resource) {
        utils.storeValues(resources[resource], service.values).then(function() {
            $('.modal').modal('hide');
            service.initView();
        }, function(result) {
            service.errors = result.data;
        });
    };

    service.openDeleteModal = function(resource, obj) {
        utils.fetchValues(resources[resource], factories[resource], obj).$promise.then(function(response) {
            service.values = response;
            service.values.children = obj.children;
            $('#' + resource + '-delete-modal').modal('show');
        });
    };

    service.submitDeleteModal = function(resource) {
        resources[resource].delete({id: service.values.id}, function() {
            $('.modal').modal('hide');
            service.initView();
        });
    };

    service.openShowModal = function(resource, obj) {
        service.values = utils.fetchValues(resources[resource], factories[resource], obj)

        $q.when(service.values.$promise).then(function() {
            $('#' + resource + '-show-modal').modal('show');
        });
    };

    service.hideAttribute = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    return service;

}])

.controller('DomainController', ['$scope', 'DomainService', function($scope, DomainService) {

    $scope.service = DomainService;
    $scope.service.init();

}]);
