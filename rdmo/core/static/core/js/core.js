angular.module('core', ['ngResource'])

.config(['$httpProvider', '$interpolateProvider', '$resourceProvider', function($httpProvider, $interpolateProvider,$resourceProvider) {

    // set Django's CSRF Cookie and Header
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';

    // use {$ and $} as tags for angular
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    // set $reosurce not to strip slashes and add an update action
    $resourceProvider.defaults.stripTrailingSlashes = false;
    $resourceProvider.defaults.actions.update = {
        method: 'PUT',
        params: {}
    };
}])

.filter('capitalize', function() {
    return function(input, scope) {
        if (angular.isDefined(input)) {
            return input.substring(0,1).toUpperCase()+input.substring(1);
        } else {
            return '';
        }
    };
})

.directive('codemirror', function() {

    return {
        scope: {
            id: '@',
            model: '='
        },
        require: 'ngModel',
        link: function(scope, element, attrs, ngModel) {
            // instanciate CodeMirror on the element
            editor = CodeMirror.fromTextArea(element[0], {
                lineNumbers: true,
                mode: attrs.mode
            });

            // whenever the user types into code mirror update the model
            editor.on('change', function(cm, change) {
                ngModel.$setViewValue(cm.getValue());
            });

            // when the model is updated update codemirror
            ngModel.$formatters.push(function(model_values) {
                if (angular.isDefined(model_values)) {
                    editor.setValue(model_values);
                }
                return model_values;
            });
        }
    };
})

.directive('formgroup', function() {

    return {
        scope: {
            id: '@',
            label: '@',
            help: '@',
            model: '=',
            errors: '=',
            warning: '=',
            options: '=',
            optionsLabel: '@',
            optionsFilter: '=',
            optionsNull: '@',
            quicksearch: '@',
            rows: '@?',
            mode: '@'
        },
        templateUrl: function(element, attrs) {
            var staticurl = angular.element('meta[name="staticurl"]').attr('content');
            return staticurl + 'core/html/formgroup_' + attrs.type + '.html';
        },
        controller: function($scope) {
            $scope.rows = angular.isDefined($scope.rows) ? $scope.rows : 4;
        },
        link: function(scope, element, attrs, ngModel) {
            element.on('refresh', function() {
                angular.element(this).find('select').each(function(key, element) {
                    angular.element(element).select2({
                        dropdownParent: angular.element(element).parent(),
                        theme: "bootstrap"
                    });
                });
            });
        }
    };
})

.directive('byNumber', function() {
    return {
        require: 'ngModel',
        link: function(scope, element, attrs, ngModel) {

            if (attrs.multiple) {

                ngModel.$parsers.push(function(view_values) {
                    if (angular.isArray(view_values)) {
                        model_values = view_values.map(function (view_value) {
                            return parseInt(view_value, 10);
                        });
                        return model_values;
                    } else {
                        return view_values;
                    }
                });

                ngModel.$formatters.push(function(model_values) {
                    if (angular.isArray(model_values)) {
                        view_values = model_values.map(function (model_value) {
                            return '' + model_value;
                        });
                        return view_values;
                    } else {
                        return model_values;
                    }
                });

            } else {

                ngModel.$parsers.push(function(view_value) {
                    if (view_value === '') {
                        return null;
                    } else {
                        return parseInt(view_value, 10);
                    }
                });

                ngModel.$formatters.push(function(model_value) {
                    if (model_value === null) {
                        return '';
                    } else {
                        return '' + model_value;
                    }
                });

            }
        }
    };
})

.directive('pending', ['$http', '$timeout', function ($http, $timeout) {
    return {
        restrict: 'E',
        template: '<i class="fa fa-circle-o-notch fa-spin fa-fw"></i>',
        link: function (scope, element, attrs) {
            scope.isPending = function () {
                return $http.pendingRequests.length > 0;
            };
            scope.$watch(scope.isPending, function (value) {
                if (value) {
                    if (angular.isUndefined(scope.promise) || scope.pending === null) {
                        scope.promise = $timeout(function(){
                            element.removeClass('ng-hide');
                        }, 300);
                    }
                } else {
                    $timeout.cancel(scope.promise);
                    scope.pending = null;
                    element.addClass('ng-hide');
                }
            });
        }
    };
}])

.factory('utils', function() {
    return {
        fetchValues: function(resource, factory, obj, create, copy) {
            if (angular.isDefined(create) && create) {
                return factory(obj);
            } else if (angular.isDefined(copy) && copy) {
                return resource.get({id: obj.id}, function(response) {
                    response.copy = true;
                });
            } else {
                return resource.get({id: obj.id});
            }
        },
        storeValues: function(resource, values) {
            if (angular.isDefined(values.removed) && values.removed) {
                if (angular.isDefined(values.id)) {
                    return resource.delete({id: values.id}).$promise;
                }
            } else {
                if (angular.isDefined(values.copy)) {
                    return resource.update({
                        id: values.id,
                        detail_action: 'copy'
                    }, values).$promise;
                } else if (angular.isDefined(values.id)) {
                    return resource.update({id: values.id}, values).$promise;
                } else {
                    return resource.save(values).$promise;
                }
            }
        }
    }
});
