// 1) CodeMirror 초기화 (전역 접근을 위해 window 객체에 저장)
window.editor = CodeMirror.fromTextArea(
  document.getElementById('editor'),
  {
    mode: 'python',            // Python 문법 강조
    theme: 'material-darker',  // 다크 테마
    lineNumbers: true,         // 줄 번호 표시
    indentUnit: 4,             // 들여쓰기 단위
    tabSize: 4,
    // autofocus: true,
    lineWrapping: true         // 긴 줄 자동 줄바꿈
  }
);

// 전역 함수로 에디터에 포커스 주기 (외부에서 호출 가능)
window.focusEditor = function() {
  if(window.editor) {
    window.editor.focus();
    // 커서를 맨 끝으로 이동
    const lastLine = window.editor.lastLine();
    const lastChar = window.editor.getLine(lastLine).length;
    window.editor.setCursor({line: lastLine, ch: lastChar});
  }
};

//가로를 그대로 두고 싶으면 첫 번째 인자에 null
editor.setSize(null, "480px");

const submitCodeBtn = document.getElementById('submitCodeBtn');
const spinner = document.getElementById('loadingSpinner');
const successIcon = document.getElementById('successIcon');
var submitCodeBtnClicked = false; //버튼 클릭 여부

// 1) 이미 초기화된 CodeMirror 인스턴스를 가정합니다.
const codeMirrorEditor = editor; // 혹은 editor 변수명

// 2) 버튼에 클릭 핸들러 등록
submitCodeBtn.addEventListener('click', async () => {

  submitCodeBtnClicked = true; // 버튼클릭완료

  // 이미 비활성화된 상태면 아무 동작도 하지 않음
  if (submitCodeBtn.disabled) return;
    // 1) 클릭 즉시 버튼 비활성화
  submitCodeBtn.disabled = true;

  // 에디터에서 코드 가져오기
  const code = codeMirrorEditor.getValue();

  // 요청 시작 시 스피너 숨김 (혹시 전 상태 남아있다면)
  spinner.classList.add('d-none');

  // 1) 요청 시작 직전 시점
  const t0 = performance.now();

  // 예: 300ms 지나도 응답이 없으면 스피너 보여주기
  const spinnerTimeout = setTimeout(() => {
    spinner.classList.remove('d-none');
    document.getElementById('submitCodeBtn').disabled = true;
  }, 300);

  try {
    // 3) fetch로 서버에 코드 전송
    const res = await fetch('/api/reward-function/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ reward_function: code })
    });

    const data = await res.json();

    // 3) 응답 도착 시점
    const t1 = performance.now();
    clearTimeout(spinnerTimeout);  // 스피너 타이머 해제
    spinner.classList.add('d-none'); // 스피너 숨김
    document.getElementById('submitCodeBtn').disabled = false; // 버튼 다시 활성화화

    // 응답 데이터 에러난 경우
    if (!res.ok) {

      // 1. JSON 파싱
      //const errData = await res.json();

      // 2. error 안에 있는 정보 꺼내서 콘솔에 출력
      console.log('error_object:', data.error);
      console.log('error_line:', data.error.error_line);
      console.log('error_message:', data.error.error_message);
      console.log('error_type:', data.error.error_type);

      //에러난 경우 
      responseOutput.textContent =`❗ An error occurred!\n\n${data.error.error_message}`;

      //에러 콘솔 표시
      document.getElementById('responseOutput').classList.remove("d-none");

      //에러 메시지창 보이기
      successIcon.classList.add('d-none');  

    } else {  //응답성공
  
       //버튼 비활성화  
       //document.getElementById('submitCodeBtn').disabled = true;

      // 성공 메시지창 아이콘 보이기
      successIcon.classList.remove('d-none');   
    }

    //  if (!res.ok) throw new Error(`서버 응답 에러: ${res.status}`);

    // 4) JSON 파싱 완료 시점
    const t2 = performance.now();

  } catch (err) {
    // 에러 시에도 타이머 해제 & 스피너 숨기기
    clearTimeout(spinnerTimeout);  // 스피너 타이머 해제
    console.error(err);
    spinner.style.display = 'none';
    document.getElementById('responseOutput').textContent =
      `에러 발생: ${data.error.error_message}`;
  }
});

// editor 변수는 CodeMirror.fromTextArea(...) 리턴값
editor.on('change', (cm, changeObj) => {
  //console.log('내용이 바뀌었어요:', cm.getValue());

  //버튼 활성화  
  document.getElementById('submitCodeBtn').disabled = false;
  // 체크 아이콘 다시 숨기기
  successIcon.classList.add('d-none'); 
 
  //에러 콘솔 표시x
  document.getElementById('responseOutput').classList.add("d-none");

  // 중요: 코드가 변경되면 검증 상태 리셋
  submitCodeBtnClicked = false;

  // 보상 함수 실시간 저장
  if (window.saveRewardFunction) {
    window.saveRewardFunction(cm.getValue());
  }

  //console.log('에디터 내부 클릭됨 at', event.clientX, event.clientY);

});

// 설정 로드 시 pendingRewardFunction이 있으면 적용
if (window.pendingRewardFunction) {
  editor.setValue(window.pendingRewardFunction);
  delete window.pendingRewardFunction;
}
