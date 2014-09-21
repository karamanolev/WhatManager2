'use strict';

angular.
    module('whatify.searchBar', ['whatify']).
    controller('SearchController', function($scope, whatMeta) {
        $scope.resultsVisible = false;
        $scope.searchQuery = '';
        $scope.search = function() {
            if ($scope.searchQuery.length > 2) {
                whatMeta.search($scope.searchQuery).success(function(response) {
                    $scope.searchResults = response;
                });
            }
        };
        $scope.hideResults = function() {
            $scope.resultsVisible = false;
        };
        $scope.showResults = function() {
            $scope.resultsVisible = true;
        }
    }).
    directive('ngWmSearchBar', function($document) {
        return {
            templateUrl: templateRoot + '/searchBar/searchBar.html',
            controller: 'SearchController',
            link: function(scope, element, attrs) {
                $document.on('click', function(e) {
                    scope.$apply(function() {
                        scope.hideResults();
                    })
                });

                element.find('.search-results, input').on('click', function(e) {
                    e.stopPropagation();
                });

                scope.$watch('resultsVisible', function(newValue, oldValue) {
                    if (newValue) {
                        element.find('.search-results').fadeIn('fast');
                    } else {
                        element.find('.search-results').fadeOut('fast');
                    }
                });
            }
        }
    })
;
