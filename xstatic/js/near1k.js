let wsess;

function getUrlParams() {
	var params = {};
	window.location.search.replace(/[?&]+([^=&]+)=([^&]*)/gi, function (str, key, value) {
		params[key] = value;
	});
	return params;
}
let params = getUrlParams();

function init() {
    const xhr = new XMLHttpRequest;
    xhr.onreadystatechange = function(){
        if (this.status == 200 && this.readyState == this.DONE) {
            var res = JSON.parse(this.responseText);
            var instr = '';
            for (var key in res) {
                if (res[key][1]==1) {
                    instr = `<div>정답은 ${key}입니다. 가장 유사한 단어는 다음과 같습니다:</div>
                    <table><tbody><tr><th>유사도 순위</th><th>단어</th><th>유사도</th></tr>`;
                } else {
                    instr += `<tr><td>${res[key][0]}</td><td>${key}</td><td>${res[key][1]}</td></th>`;
                }
            }
            instr += `</tbody></table>`;
            document.getElementById('list').innerHTML = instr;
        } else if (this.status != 200 && this.readyState == this.DONE) {
            alert("오류가 발생했습니다.");
        }
    };
    xhr.open("GET", "/near1k");
    xhr.setRequestHeader("word-sess", wsess);
    xhr.send();
};

window.onload = () => {
    if ('s' in params) {
        const xhr = new XMLHttpRequest;
        xhr.onreadystatechange = function(){
            if (this.status == 200 && this.readyState == this.DONE) {
                var res = JSON.parse(this.responseText);
                wsess = res.sess;
                init();
            } else if (this.status != 200 && this.readyState == this.DONE) {
                alert('세션 ID가 잘못되었습니다. 메인 페이지로 이동합니다.');
                window.location.href="/static/select.html";
                return;
            }
        };
        xhr.open("GET", "/check");
        xhr.setRequestHeader("word-sess", params['s']);
        xhr.send();
    } else {
        alert('세션 ID가 잘못되었습니다. 메인 페이지로 이동합니다.');
        window.location.href="/static/select.html";
        return;
    }
}