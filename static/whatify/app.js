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
            this.getTorrentGroup = function(id, defeatCache, loadFromWhat) {
                var torrentGroupUrl = 'torrent_groups/' + id,
                    options = {
                        cache: true
                    };
                if (defeatCache) {
                    $httpDefaultCache.remove(torrentGroupUrl);
                    if (loadFromWhat) {
                        options.headers = {
                            'X-Refresh': 'true'
                        };
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
            this.getArtist = function(id, defeatCache, loadFromWhat) {
                var artistUrl = 'artists/' + id;
                var options = {
                    cache: true
                };
                if (defeatCache) {
                    $httpDefaultCache.remove(artistUrl);
                    if (loadFromWhat) {
                        options.headers = {
                            'X-Refresh': 'true'
                        };
                    }
                }
                return $http.get(artistUrl, options);
            };
            this.downloadTorrentGroup = function(id) {
                return $http.get('torrent_groups/' + id + '/download');
            };
        };
    }).
    factory('whatifyNoty', function() {
        var s = {};
        s.success = function(text) {
            noty({
                text: text,
                type: 'success',
                timeout: 5000
            });
        };
        s.error = function(text) {
            noty({
                text: text,
                type: 'error',
                timeout: 30000
            });
        };
        s.info = function(text, timeout) {
            noty({
                text: text,
                type: 'alert',
                timeout: timeout || 3000
            });
        };
        return s;
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
    filter('isNumber', function() {
        return function(value) {
            return angular.isNumber(value);
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
    directive('percentageProgressBar', function() {
        return {
            template: '<div class="number-pb"><div class="number-pb-shown"></div>' +
                '<div class="number-pb-num">0%</div></div>',
            scope: {
                value: '='
            },
            link: function(scope, element, attrs) {
                var progressBar = $('.number-pb').NumberProgressBar({
                    style: 'percentage',
                    min: 0,
                    max: 100,
                    duration: 3000,
                    current: scope.value || 0
                });
                window.pb = progressBar;
                scope.$watch('value', function() {
                    progressBar.reach(scope.value, {
                        duration: 1000
                    });
                });
            }
        }
    }).
    directive('copyLinkModal', function() {
        return {
            template: '<div class="modal modal-dark fade" tabindex="-1" role="dialog" aria-hidden="true">' +
                '<div class="modal-dialog"><div class="modal-content"><div class="modal-header">' +
                '<h4 class="modal-title" id="myModalLabel">Modal title</h4></div><div class="modal-body">' +
                '<input type="text" class="form-control"></span></div><div class="modal-footer">' +
                '<button type="button" class="btn btn-whatify" data-dismiss="modal">Close</button>' +
                '</div></div></div></div>',
            controller: function($scope, $rootScope) {
                var removeHandler = $rootScope.$on('showCopyLinkModal', function(event, params) {
                    $scope.showModal(params);
                });
                $scope.$on('$destroy', function() {
                    removeHandler();
                });
            },
            replace: true,
            link: function(scope, element, attrs) {
                scope.showModal = function(params) {
                    var inputField = element.find('.form-control');
                    element.find('.modal-title').text(params.title);
                    inputField.val(params.url);
                    element.modal({
                    });
                };
            }
        }
    }).
    config(function($routeProvider) {
        $routeProvider.otherwise({redirectTo: '/'})
    })
;
