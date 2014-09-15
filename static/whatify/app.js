'use strict';

angular.
    module('whatify', [
        'ngRoute',
        'whatify.home',
        'whatify.player',
        'whatify.searchBar'
    ]).
    factory('whatMeta', function($q, $http, $cacheFactory) {
        var $httpDefaultCache = $cacheFactory.get('$http');
        return new function() {
            this.getTorrentGroup = function(id, defeatCache) {
                var torrentGroupUrl = 'torrent_groups/' + id;
                var options = {
                    cache: true
                };
                if (defeatCache) {
                    $httpDefaultCache.remove(torrentGroupUrl);
                    options.headers = {
                        'X-Refresh': 'true'
                    }
                }
                return $http.get(torrentGroupUrl, options);
            };
            this.searchCanceller = null;
            this.search = function(query) {
                if (this.searchCanceller) {
                    this.searchCanceller.resolve('New search coming');
                }
                this.searchCanceller = $q.defer();
                return $http.get('search/' +
                        encodeURIComponent(query), {timeout: this.searchCanceller.promise}
                );
            };
            this.getArtist = function(id, defeatCache) {
                var artistUrl = 'artists/' + id;
                var options = {
                    cache: true
                };
                if (defeatCache) {
                    $httpDefaultCache.remove(artistUrl);
                    options.headers = {
                        'X-Refresh': 'true'
                    }
                }
                return $http.get(artistUrl, options);
            };
        };
    }).
    filter('trustAsHtml', function($sce) {
        return function(input) {
            return $sce.trustAsHtml(input);
        };
    }).
    filter('asPercent', function() {
        return function(value) {
            return Math.floor(value * 100) + '%';
        };
    }).
    filter('asTime', function() {
        return function(value) {
            if (value === null) {
                return '-:--';
            }
            var seconds = Math.floor(value % 60);
            var minutes = Math.floor(value / 60);
            return minutes + ':' + (seconds < 10 ? '0' + seconds : seconds);
        }
    }).
    directive('mainPaneSpinner', function($rootScope) {
        $rootScope.mainSpinner = {
            visible: true
        };
        return {
            template: '<div id="main-pane-spinner" ng-show="mainSpinner.visible"></div>',
            replace: true,
            link: function(scope, element, attrs) {
                var spinner = new Spinner({
                    color: '#ffffff'
                }).spin(element[0]);
            }
        }
    }).
    config(function($routeProvider) {
        $routeProvider.otherwise({redirectTo: '/'})
    })
;
