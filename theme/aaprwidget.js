/**
 * Created by superdesk on 8/17/22.
 */
var widget = {
    get_params: function () {
        var map = {};
        var source = window.location.search;
        if ("" != source) {
            var groups = source.substr(1).split("&"), i;
            for (i in groups) {
                if (typeof groups[i] === 'string') {
                    i = groups[i].split("=");
                    map[decodeURIComponent(i[0])] = decodeURIComponent(i[1]);
                }
            }
        }
        return map;
    },

    get_url: function() {
        var url = 'http://localhost:5050/releases';
        var params = this.get_params();
        if (params['rkey']) {
            url += ('/' + params['rkey']);
        } else {
            if (params['from']) {
                url += ('?from=' + params['from']);
            };
        }
        return url;
    },

    get_pr: function () {
            ajax = new XMLHttpRequest();
            ajax.onreadystatechange = function () {
                if (ajax.readyState > 3 && ajax.status == 200) {
                    document.getElementById("aapr-widget").innerHTML = ajax.responseText;
                }
            }
            ajax.open('GET', this.get_url(), true);
            setTimeout(function () {
                ajax.send();
            }, 0);
    }
}
widget.get_pr();