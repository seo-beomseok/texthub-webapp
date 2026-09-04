# GitHub Pages 배포 방법

이 폴더는 기존 Dash/Python 웹앱을 **정적 GitHub Pages 웹사이트**로 변환한 결과입니다. 배포 후에는 AWS EC2, Flask, Dash, Gunicorn, Python 서버가 필요하지 않습니다.

## 1. GitHub 저장소 생성

예를 들어 저장소 이름을 다음과 같이 만듭니다.

```text
financial-indices
```

## 2. ZIP을 푼 뒤 파일 업로드

ZIP 내부의 파일들을 저장소의 최상위(root)에 그대로 올립니다.

```text
index.html
.nojekyll
assets/
js/
data/
vendor/
tools/
README.md
```

`index.html`이 저장소 root에 있어야 가장 간단합니다.

## 3. GitHub Pages 활성화

GitHub 저장소에서 다음 순서로 이동합니다.

**Settings → Pages → Build and deployment → Deploy from a branch**

그리고 다음을 선택합니다.

- Branch: `main`
- Folder: `/ (root)`

저장하면 다음 형태의 주소에서 사이트가 열립니다.

```text
https://사용자이름.github.io/financial-indices/
```

모든 데이터 경로를 상대경로로 작성했으므로 repository 이름이 달라도 별도의 코드 수정이 필요하지 않습니다.

## 4. 동적 기능

GitHub Pages에서도 다음 기능이 브라우저에서 그대로 동작합니다.

- Plotly hover
- zoom / pan
- legend on/off
- News 기간/분야 dropdown
- Market 분야 dropdown
- Factor 산업 dropdown
- Event / Impact / Evaluation dropdown
- News range slider
- Treemap max-depth slider
- 반응형 그래프

이 기능들은 모두 `js/app.js`와 `vendor/plotly.min.js`가 브라우저에서 처리하므로 Python 서버가 필요하지 않습니다.

## 5. 로컬에서 확인하는 방법

브라우저에서 `index.html`을 직접 더블클릭하면 보안 정책 때문에 `fetch()`가 막힐 수 있습니다. 폴더에서 다음을 실행하세요.

```bash
python -m http.server 8000
```

그 다음 브라우저에서 다음 주소를 엽니다.

```text
http://localhost:8000/
```

## 6. 데이터 업데이트

향후 원래 Python 분석 코드로 새로운 `out/*.csv`를 생성했다면 웹서버를 다시 만들 필요는 없습니다. JSON만 다시 만들어 GitHub에 올리면 됩니다.

```bash
pip install -r requirements-build.txt
python tools/build_data.py --src ../원본프로젝트폴더
```

`--src` 폴더 안에는 원래 프로젝트의 `out/` 디렉터리가 있어야 합니다.

## 참고

현재 ZIP의 데이터는 사용자가 제공한 `src.zip`에 들어 있던 시점의 데이터를 그대로 변환한 것입니다. 새 데이터를 임의로 추가하지 않았습니다.

수식 표현용 MathJax만 외부 CDN에서 불러옵니다. MathJax 로딩이 실패해도 Plotly 그래프와 dashboard 기능은 로컬에 포함된 JavaScript로 동작합니다.
