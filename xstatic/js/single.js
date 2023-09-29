let guesses = [];
let gameOver = false;
let chrono_forward = 1;
let guessCount = 0;
let wsess = "";
let guessed = new Set();
let similarityStory = null;

function $(id) {
    if (id.charAt(0) !== '#') return false;
    return document.getElementById(id.substring(1));
}

function guessRow(similarity, oldGuess, percentile, guessNumber, guess) {
    let percentileText = percentile;
    let progress = "";
    let closeClass = "";
    if (similarity >= similarityStory.rest * 100 && percentile === '1000위 이상') {
        percentileText = '<span class="weirdWord">????<span class="tooltiptext">이 단어는 사전에는 없지만, 데이터셋에 포함되어 있으며 1,000위 이내입니다.</span></span>';
    }
    if (typeof percentile === 'number') {
            closeClass = "close";
            percentileText = `<span class="percentile">${percentile}</span>&nbsp;`;
            progress = ` <span class="progress-container">
<span class="progress-bar" style="width:${(1001 - percentile)/10}%">&nbsp;</span>
</span>`;
    }
    let style = '';
    if (oldGuess === guess) {
        style = 'style="color: #f7617a;font-weight: 600;"';
    }
    return `<tr><td>${guessNumber}</td><td ${style}>${oldGuess}</td><td>${similarity.toFixed(2)}</td><td class="${closeClass}">${percentileText}${progress}
</td></tr>`;
}

function endGame(won) {
    gameOver = true;
    let response;
    if (won) {
        response = `정답 단어를 맞혔습니다. ${guesses.length}번째 추측만에 정답을 맞혔네요!`;
    } else {
        response = `${guesses.length - 1}번째 추측에서 포기했습니다!`;
    }
    response += '<div class="padt"></div><div class="ibm sml btn3" onclick="window.location.href='+"'/static/single.html'"+';">다시 하기</div>';
    $('#win').innerHTML = response;
    $('#win').style.display = "block";
}

function submit() {
    w = $('#stxt').value.trim();
    $('#stxt').value = "";
    if (w=="") return;
    const xhr = new XMLHttpRequest;
    xhr.onreadystatechange = function(){
        if (this.status == 200 && this.readyState == this.DONE) {
            var res = JSON.parse(this.responseText);
            $('#error').textContent = '';
            guess = res.guess
            let percentile = res.rank;
            let similarity = res.sim * 100.0;
            if (!guessed.has(guess)) {
                guessCount += 1;
                guessed.add(guess);
                const newEntry = [similarity, guess, percentile, guessCount];
                guesses.push(newEntry);
            }
            guesses.sort(function(a, b){return b[0]-a[0]});
            chrono_forward = 1;
            updateGuesses(guess);
            if (res.sim == 1 && !gameOver) {
                endGame(true);
            }
        } else if (this.status == 404 && this.readyState == this.DONE) {
            var res = JSON.parse(this.responseText);
            if (res.error == "unknown") {
                $('#error').textContent = `${w}은(는) 알 수 없는 단어입니다.`;
                return;
            }
            return;
        } else if (this.status != 200 && this.readyState == this.DONE) {
            alert("오류가 발생했습니다.");
            return;
        }
    };
    xhr.open("GET", "/single/guess?word="+w);
    xhr.setRequestHeader("word-sess", wsess);
    xhr.send();
}

function updateGuesses(guess) {
    let inner = `<tr><th id="chronoOrder">#</th><th id="alphaOrder">추측한 단어</th><th id="similarityOrder">유사도</th><th>유사도 순위</th></tr>`;
    /* This is dumb: first we find the most-recent word, and put
       it at the top.  Then we do the rest. */
    for (let entry of guesses) {
        let [similarity, oldGuess, percentile, guessNumber] = entry;
        if (oldGuess == guess) {
            inner += guessRow(similarity, oldGuess, percentile, guessNumber, guess);
        }
    }
    inner += "<tr><td colspan=4><hr></td></tr>";
    for (let entry of guesses) {
        let [similarity, oldGuess, percentile, guessNumber] = entry;
        if (oldGuess != guess) {
            inner += guessRow(similarity, oldGuess, percentile, guessNumber);
        }
    }
    $('#guesses').innerHTML = inner;
    $('#chronoOrder').addEventListener('click', event => {
        guesses.sort(function(a, b){return chrono_forward * (a[3]-b[3])});
        chrono_forward *= -1;
        updateGuesses(guess);
    });
    $('#alphaOrder').addEventListener('click', event => {
        guesses.sort(function(a, b){return a[1].localeCompare(b[1])});
        chrono_forward = 1;
        updateGuesses(guess);
    });
    $('#similarityOrder').addEventListener('click', event => {
        guesses.sort(function(a, b){return b[0]-a[0]});
        chrono_forward = 1;
        updateGuesses(guess);
    });
}

function getSimilarityStory() {
    const xhr = new XMLHttpRequest;
    xhr.onreadystatechange = function(){
        if (this.status == 200 && this.readyState == this.DONE) {
            var res = JSON.parse(this.responseText);
            similarityStory = res;
            $('#similarity-story').innerHTML = `
            꼬맨틀의 정답 단어를 맞혀보세요.<br/>
            정답 단어와 가장 유사한 단어의 유사도는 <b>${(similarityStory.top * 100).toFixed(2)}</b> 입니다.
            10번째로 유사한 단어의 유사도는 ${(similarityStory.top10 * 100).toFixed(2)}이고,
            1,000번째로 유사한 단어의 유사도는 ${(similarityStory.rest * 100).toFixed(2)} 입니다.`;
        } else if (this.status != 200 && this.readyState == this.DONE) {
            alert("오류가 발생했습니다.");
            return;
        }
    };
    xhr.open("GET", "/similarity");
    xhr.setRequestHeader("word-sess", wsess);
    xhr.send();
}

function init() {
    $('#sbtn').onclick = function(){submit();};
    document.addEventListener("keyup", function(event) {
        if (event.key === 'Enter') {
            submit();
        }
    });
    const xhr = new XMLHttpRequest;
    xhr.onreadystatechange = function(){
        if (this.status == 200 && this.readyState == this.DONE) {
            var res = JSON.parse(this.responseText);
            wsess = res.sess;
            $('#sess').innerText = "현재 세션 ID: "+wsess;
            getSimilarityStory();
        } else if (this.status != 200 && this.readyState == this.DONE) {
            alert("오류가 발생했습니다.");
        }
    };
    xhr.open("GET", "/single/start");
    xhr.send();
    $('#gubtn').addEventListener('click', function(event) {
        if (guessCount && !gameOver) {
            if (confirm("정말로 포기하시겠습니까?")) {
                const xhr = new XMLHttpRequest;
                xhr.onreadystatechange = function(){
                    if (this.status == 200 && this.readyState == this.DONE) {
                        var res = JSON.parse(this.responseText);
                        secret = res.word;
                        guessed.add(secret);
                        guessCount += 1;
                        const newEntry = [100, secret, '정답', guessCount];
                        guesses.push(newEntry);
                        guesses.sort(function(a, b){return b[0]-a[0]});
                        updateGuesses(guess);
                        endGame(false);
                    }
                    if (this.status != 200 && this.readyState == this.DONE) {
                        alert("오류가 발생했습니다.");
                    }
                }
                xhr.open("GET", "/giveup");
                xhr.setRequestHeader("word-sess", wsess);
                xhr.send();
            }
        } else if (!gameOver) {
            alert("아직 포기하기엔 이릅니다!");
        }
    });
};

window.onload = () => {
    init();   
}