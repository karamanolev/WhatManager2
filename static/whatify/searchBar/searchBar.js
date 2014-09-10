'use strict';

angular.
    module('whatify.searchBar', ['whatify']).
    controller('SearchController', function($scope, WhatMeta) {
        $scope.searchQuery = '';
        $scope.search = function () {
            if ($scope.searchQuery.length > 2) {
                WhatMeta.searchTorrentGroups($scope.searchQuery).success(function (response) {
                    $scope.torrentGroups = response;
                });
                WhatMeta.searchArtists($scope.searchQuery).success(function (response) {
                    $scope.artists = response;
                });
            } else {
                $scope.torrentGroups = [];
                $scope.artists = [];
            }
        };
    }).
    directive('ngWmSearchBar', function () {
        return {
            'templateUrl': 'searchBar/searchBar.html',
            'controller': 'SearchController'
        }
    })
;
