document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('theme-toggle');
    const body = document.body;
    const dbButtons = document.querySelectorAll('.db-btn');
    const databaseForms = document.querySelectorAll('.database-form');
  
    // Theme Toggle Functionality
    themeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-theme');
      body.classList.toggle('light-theme');
      
      const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
      localStorage.setItem('theme', currentTheme);
    });
  
    // Check and Apply Saved Theme on Load
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
      body.classList.remove('dark-theme');
      body.classList.add('light-theme');
    }
  
    // Database Selection Functionality
    dbButtons.forEach(button => {
      button.addEventListener('click', () => {
        const targetFormId = button.getAttribute('data-target');
        
        // Hide all forms
        databaseForms.forEach(form => {
          form.classList.remove('active');
        });
  
        // Show selected form
        const targetForm = document.getElementById(targetFormId);
        targetForm.classList.add('active');
      });
    });
  });