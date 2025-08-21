// حفظ الاسم في LocalStorage وعرضه
const nameForm = document.getElementById('nameForm');
const savedNameP = document.getElementById('savedName');
const callApiBtn = document.getElementById('callApi');
const apiResult = document.getElementById('apiResult');

function loadSavedName() {
  const name = localStorage.getItem('demo:name');
  if (name) savedNameP.textContent = `الاسم المحفوظ: ${name}`;
}

nameForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const name = new FormData(nameForm).get('name');
  localStorage.setItem('demo:name', name);
  savedNameP.textContent = `الاسم المحفوظ: ${name}`;
});

callApiBtn.addEventListener('click', async () => {
  apiResult.textContent = '...جاري النداء';
  try {
    const res = await fetch('/api/hello');
    const data = await res.json();
    apiResult.textContent = JSON.stringify(data, null, 2);
  } catch (e) {
    apiResult.textContent = 'تعذّر الاتصال بـ /api/hello. تأكد من النشر على Vercel.';
  }
});

loadSavedName();
