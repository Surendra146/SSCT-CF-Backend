import { chromium } from 'file:///D:/Devlopment%20files/Project%20files/Frontend%20code/ssct-Frontend%20CF/node_modules/playwright-core/index.mjs';
const browser=await chromium.launch({channel:'msedge',headless:true});
const context=await browser.newContext({viewport:{width:1440,height:960}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
async function login(){await page.goto('http://localhost:5174/admin/login');await page.locator('[name=username]').fill('qa-admin');await page.locator('[name=password]').fill('qa-password-only-123');await page.getByRole('button',{name:'Sign in securely'}).click();await page.waitForURL('**/admin/dashboard');}
await login();
const suffix=Date.now();
async function createProgram(kind){
 await page.getByRole('link',{name:kind==='batches'?'Batches':'Internship Programs',exact:true}).click();
 await page.getByRole('button',{name:kind==='batches'?'Add batch':'Add program',exact:true}).click();
 const id=`qa-${kind}-${suffix}`;
 await page.getByLabel(/^Name/).fill(`QA ${kind} ${suffix}`);
 await page.getByLabel('Stable slug').fill(id);
 await page.getByLabel('Publication status').selectOption('published');
 await page.getByLabel('Short description').fill('Isolated browser acceptance test program.');
 await page.getByLabel('Duration (for example, 6 weeks)').fill('6 weeks');
 await page.getByLabel('Related course').selectOption('python-full-stack');
 await page.getByLabel('Start date',{exact:true}).fill('2099-01-01');
 await page.getByLabel('End date',{exact:true}).fill('2099-02-15');
 await page.getByLabel(/^Branch/).selectOption('Tarnaka');
 if(kind==='batches'){
  await page.getByLabel('Start time',{exact:true}).fill('10:00');await page.getByLabel('End time',{exact:true}).fill('12:00');
  await page.getByLabel('Schedule days').fill('Monday');await page.getByLabel('Schedule days').press('Enter');
 }else{
  await page.getByLabel('Skills students will learn').fill('Python,FastAPI');await page.getByLabel('Skills students will learn').press('Enter');
 }
 await page.getByRole('button',{name:'Save changes'}).click();
 await page.locator('dialog').waitFor({state:'detached'});
 console.log('Created published',kind,'via admin form.');return id;
}
const batch=await createProgram('batches');const internship=await createProgram('internships');
await page.goto('http://localhost:5174/batches');await page.getByRole('button',{name:/Upcoming Batches/}).click();
const card=page.locator('.live-program-card').filter({hasText:`QA batches ${suffix}`});await card.waitFor();
await card.getByRole('link',{name:'Register Now'}).click();await page.waitForURL('**/enroll?**');
await page.getByRole('status').filter({hasText:`QA batches ${suffix}`}).waitFor();
await page.getByLabel('Full name',{exact:false}).fill('QA Browser Student');await page.getByLabel('Mobile number',{exact:false}).fill('9876543210');await page.getByLabel('Qualification',{exact:false}).fill('BTech');
await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Submit registration'}).click();
await page.getByRole('status').filter({hasText:'Your registration request was received.'}).waitFor();console.log('Public linked batch registration succeeded.');
await page.goto('http://localhost:5174/internship');await page.getByRole('button',{name:/Upcoming Programs/}).click();
const internshipCard=page.locator('.live-program-card').filter({hasText:`QA internships ${suffix}`});await internshipCard.waitFor();await internshipCard.getByRole('link',{name:'Apply Now'}).click();
await page.getByRole('status').filter({hasText:`QA internships ${suffix}`}).waitFor();await page.getByLabel('Full name',{exact:false}).fill('QA Internship Applicant');await page.getByLabel('Mobile number',{exact:false}).fill('9876543211');await page.getByLabel('Qualification',{exact:false}).fill('BTech');await page.getByLabel('Preferred batch',{exact:false}).selectOption('Weekend');await page.getByRole('checkbox').check();await page.getByRole('button',{name:'Submit registration'}).click();await page.getByRole('status').filter({hasText:'Your registration request was received.'}).waitFor();console.log('Public linked internship application succeeded.');
await login();await page.getByRole('link',{name:'Registrations',exact:true}).click();await page.getByText('QA Browser Student',{exact:true}).waitFor();await page.getByRole('button',{name:'Edit QA Browser Student'}).click();await page.getByLabel(/^Status/).selectOption('Contacted');await page.getByLabel('Internal notes').fill('Browser test follow-up');await page.getByRole('button',{name:'Save changes'}).click();await page.locator('dialog').waitFor({state:'detached'});console.log('Registration status and notes update succeeded.');
await page.getByRole('link',{name:'Internship Programs',exact:true}).click();await page.getByRole('button',{name:/Applications/}).click();await page.getByText('QA Internship Applicant',{exact:true}).waitFor();console.log('Application appears in internship module.');
await page.getByRole('link',{name:'Dashboard',exact:true}).click();await page.waitForTimeout(500);await page.screenshot({path:'artifacts/admin-redesign/dashboard-with-test-records.png',fullPage:true});
await page.setViewportSize({width:768,height:1024});await page.screenshot({path:'artifacts/admin-redesign/dashboard-tablet-test.png',fullPage:true});
console.log('Runtime errors:',errors);if(errors.length)throw new Error(errors.join('\n'));await browser.close();
