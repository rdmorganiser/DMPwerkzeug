angular.module('views', ['core'])

.factory('ViewsService', ['$resource', '$timeout', '$window', '$q', 'utils', '$sce', function($resource, $timeout, $window, $q, utils, $sce) {

    /* get the base url */

    var baseurl = angular.element('meta[name="baseurl"]').attr('content');

    /* configure resources */

    var resources = {
        views: $resource(baseurl + 'api/v1/views/views/:list_action/:id/:detail_action/'),
        catalogs: $resource(baseurl + 'api/v1/questions/catalogs/index/'),
        settings: $resource(baseurl + 'api/v1/core/settings/'),
        sites: $resource(baseurl + 'api/v1/core/sites/'),
        groups: $resource(baseurl + 'api/v1/core/groups/'),
    };

    /* configure factories */

    var factories = {
        views: function(parent) {
            return {
                template: '',
                uri_prefix: (angular.isDefined(parent) && parent) ? parent.uri_prefix : service.settings.default_uri_prefix,
                sites: [1]
            };
        }
    };

    /* create the tasks service */

    var service = {};

    service.init = function(options) {
        service.settings = resources.settings.get();
        service.sites = resources.sites.query();
        service.groups = resources.groups.query();
        service.uri_prefixes = []
        service.uri_prefix = ''
        service.filter = sessionStorage.getItem('views_filter') || '';

        service.initView().then(function () {
            var current_scroll_pos = sessionStorage.getItem('views_scroll_pos');
            if (current_scroll_pos) {
                $timeout(function() {
                    $window.scrollTo(0, current_scroll_pos);
                });
            }
        });

        $window.addEventListener('beforeunload', function() {
            sessionStorage.setItem('views_scroll_pos', $window.scrollY);
            sessionStorage.setItem('views_filter', service.filter);
        });
    };

    service.initView = function(options) {
        return resources.views.query({list_action: 'index'}, function(response) {
            service.views = response;
            service.uri_prefixes = response.reduce(function(list, item) {
                if (list.indexOf(item.uri_prefix) < 0) {
                    list.push(item.uri_prefix)
                }
                return list
            }, [])

            // mark help safe
            service.views.map(function(view) {
                view.help_html = $sce.trustAsHtml(view.help);
            });
        }).$promise;
    };

    service.openFormModal = function(resource, obj, create, copy) {
        service.errors = {};
        service.values = utils.fetchValues(resources['views'], factories['views'], obj, create, copy);
        service.catalogs = resources.catalogs.query();

        $q.all([
            service.values.$promise,
            service.catalogs.$promise
        ]).then(function() {
            if (service.values.template === ''){
                service.values.template = '{% load view_tags %}'
            };
            $('#' + resource + '-form-modal').modal('show');
            angular.element('.CodeMirror')[0].CodeMirror.refresh();
        });
    };

    service.submitFormModal = function(resource, close) {
        if (angular.isDefined(service.editor)) {
            service.values.template = service.editor.getValue();
        }

        utils.storeValues(resources['views'], service.values).then(function() {
            service.errors = {};

            if (angular.isUndefined(close) || close) {
                $('#' + resource + '-form-modal').modal('hide');
                service.initView();
            }
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
            $('#' + resource + '-delete-modal').modal('hide');
            service.initView();
        });
    };

    service.hideView = function(item) {
        if (service.filter && item.uri.indexOf(service.filter) < 0
                           && item.title.indexOf(service.filter) < 0
                           && item.help.indexOf(service.filter) < 0) {
            return true;
        }
        if (service.uri_prefix && item.uri_prefix != service.uri_prefix) {
            return true;
        }
    };

    return service;

}])

.controller('ViewsController', ['$scope', 'ViewsService', function($scope, ViewsService) {

    $scope.service = ViewsService;
    $scope.service.init();

}]);
