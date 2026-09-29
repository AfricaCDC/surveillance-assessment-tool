const $=selector=>document.querySelector(selector);
let setupRequired=false;

async function request(path,options={}){
  const response=await fetch(path,{headers:{'Content-Type':'application/json'},...options});
  const data=await response.json();
  if(!response.ok)throw new Error(data.error||'Request failed');
  return data;
}

function showForm(setup){
  setupRequired=setup;
  $('#login-loading').classList.add('hidden');
  $('#login-form').classList.remove('hidden');
  $('#display-name-field').classList.toggle('hidden',!setup);
  $('#confirm-field').classList.toggle('hidden',!setup);
  $('#password-requirements').classList.toggle('hidden',!setup);
  $('#login-step').textContent=setup?'FIRST-RUN SETUP':'SECURE SIGN IN';
  $('#login-title').textContent=setup?'Create administrator account':'Welcome back';
  $('#login-help').textContent=setup?'Create the first administrator account using a username or email address.':'Enter your username or email address and password to continue.';
  $('#login-submit').textContent=setup?'Create account and continue':'Sign in';
  $('#password').autocomplete=setup?'new-password':'current-password';
  $('#username').focus();
}

function showError(message){$('#login-error').textContent=message;$('#login-error').classList.remove('hidden')}

function passwordRules(password){return{length:password.length>=6,upper:/[A-Z]/.test(password),lower:/[a-z]/.test(password),number:/[0-9]/.test(password),symbol:/[^A-Za-z0-9]/.test(password)}}
function updatePasswordFeedback(){if(!setupRequired)return;const rules=passwordRules($('#password').value);Object.entries(rules).forEach(([name,met])=>{document.querySelector(`[data-rule="${name}"]`).classList.toggle('met',met)});$('#password-valid').classList.toggle('hidden',!Object.values(rules).every(Boolean))}

document.addEventListener('DOMContentLoaded',async()=>{
  try{
    const status=await request('/api/auth/status');
    showForm(status.setup_required);
  }catch(error){$('#login-loading').textContent='Could not connect to the application.';showError(error.message)}
});

$('#login-form').addEventListener('submit',async event=>{
  event.preventDefault();
  $('#login-error').classList.add('hidden');
  const password=$('#password').value;
  if(setupRequired&&password!==$('#confirm-password').value){showError('The passwords do not match');return}
  if(setupRequired&&!Object.values(passwordRules(password)).every(Boolean)){showError('Please meet all password requirements');return}
  const button=$('#login-submit');button.disabled=true;button.classList.add('busy');button.textContent=setupRequired?'Creating account…':'Signing in…';
  try{
    const payload={username:$('#username').value,password,display_name:$('#display-name').value};
    await request(setupRequired?'/api/auth/setup':'/api/auth/login',{method:'POST',body:JSON.stringify(payload)});
    location.replace('/app');
  }catch(error){showError(error.message);button.disabled=false;button.classList.remove('busy');button.textContent=setupRequired?'Create account and continue':'Sign in'}
});
$('#password').addEventListener('input',updatePasswordFeedback);
