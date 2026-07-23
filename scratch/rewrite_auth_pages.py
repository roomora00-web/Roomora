import os

base_template = """{% extends "accounts/base_auth.html" %}
{% load static %}

{% block title %}{{TITLE}} — Roomora{% endblock %}

{% block extra_css %}
<style>
  body {
    background: #0A0A0A;
    color: #FFFFFF;
    font-family: 'Plus Jakarta Sans', sans-serif;
  }
  
  .glass-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
  }

  /* Form overrides */
  input[type="email"],
  input[type="password"],
  input[type="text"] {
    width: 100%;
    background: rgba(0, 0, 0, 0.2) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #FFFFFF !important;
    padding: 0.875rem 1rem !important;
    border-radius: 0.75rem !important;
    font-size: 0.875rem !important;
    transition: all 0.2s ease !important;
    outline: none !important;
    box-shadow: none !important;
  }
  
  input[type="email"]:focus,
  input[type="password"]:focus,
  input[type="text"]:focus {
    border-color: rgba(255, 255, 255, 0.3) !important;
    background: rgba(0, 0, 0, 0.4) !important;
  }

  input::placeholder {
    color: rgba(255, 255, 255, 0.3) !important;
  }

  .ambient-glow {
    position: absolute;
    width: 600px;
    height: 600px;
    background: radial-gradient(circle, rgba(255,255,255,0.03) 0%, rgba(0,0,0,0) 70%);
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: -1;
    pointer-events: none;
  }
</style>
{% endblock %}

{% block content %}
<div class="min-h-screen w-full flex items-center justify-center relative overflow-hidden px-4 py-12">
  <div class="ambient-glow"></div>
  
  <div class="glass-card w-full max-w-md rounded-3xl p-8 sm:p-10 shadow-2xl relative z-10 text-center">
    
    <!-- Logo -->
    <div class="flex justify-center mb-8">
      <a href="{% url 'landing:home' %}" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
        <div class="h-10 w-10 bg-white rounded-xl flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0A0A0A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        </div>
        <span class="text-2xl font-bold tracking-tight text-white">Roomora</span>
      </a>
    </div>

    {{CONTENT}}

  </div>
</div>
{% endblock %}
"""

pages = {
    "forgot_password.html": {
        "title": "Forgot Password",
        "content": """
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Reset Password</h1>
      <p class="text-white/50 text-sm">Enter your email and we'll send you a link to reset your password.</p>
    </div>

    {% if messages %}
    <div class="mb-6 space-y-2 text-left">
      {% for message in messages %}
      <div class="p-4 rounded-xl text-sm font-medium border {% if message.tags == 'error' %}bg-red-500/10 border-red-500/20 text-red-400{% else %}bg-green-500/10 border-green-500/20 text-green-400{% endif %}">
        {{ message }}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <form method="post" action="{% url 'accounts:forgot-password' %}" class="space-y-5 text-left">
      {% csrf_token %}
      
      <div class="space-y-1.5">
        <label class="block text-sm font-medium text-white/80 pl-1">Email address</label>
        <input type="email" name="email" placeholder="name@example.com" required>
      </div>
      
      <button type="submit" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center mt-2">
        Send Reset Link
      </button>
    </form>
    
    <div class="mt-8 text-center border-t border-white/10 pt-6">
      <a href="{% url 'accounts:login' %}" class="text-sm font-semibold text-white/60 hover:text-white transition-colors">← Back to Sign In</a>
    </div>
"""
    },
    
    "reset_password.html": {
        "title": "Set New Password",
        "content": """
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Set New Password</h1>
      <p class="text-white/50 text-sm">Choose a strong password to secure your account.</p>
    </div>

    {% if messages %}
    <div class="mb-6 space-y-2 text-left">
      {% for message in messages %}
      <div class="p-4 rounded-xl text-sm font-medium border {% if message.tags == 'error' %}bg-red-500/10 border-red-500/20 text-red-400{% else %}bg-green-500/10 border-green-500/20 text-green-400{% endif %}">
        {{ message }}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <form method="post" action="{% url 'accounts:reset-password' token=token %}" class="space-y-5 text-left">
      {% csrf_token %}
      
      <div class="space-y-1.5">
        <label class="block text-sm font-medium text-white/80 pl-1">New Password</label>
        <input type="password" name="new_password" placeholder="••••••••" required>
      </div>
      
      <div class="space-y-1.5">
        <label class="block text-sm font-medium text-white/80 pl-1">Confirm Password</label>
        <input type="password" name="confirm_password" placeholder="••••••••" required>
      </div>
      
      <button type="submit" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center mt-2">
        Update Password
      </button>
    </form>
"""
    },

    "check_email.html": {
        "title": "Check Your Email",
        "content": """
    <div class="mb-8">
      <div class="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"></path></svg>
      </div>
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Check your email</h1>
      <p class="text-white/50 text-sm mb-6">We've sent a link to your email address. Please click the link to verify your account or reset your password.</p>
    </div>

    <a href="{% url 'accounts:login' %}" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center">
      Return to Login
    </a>
"""
    },

    "verify_email.html": {
        "title": "Email Verification",
        "content": """
    <div class="mb-8">
      {% if success %}
      <div class="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>
      </div>
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Email Verified!</h1>
      <p class="text-white/50 text-sm mb-6">Your email address has been successfully verified. You can now sign in to your account.</p>
      <a href="{% url 'accounts:login' %}" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center">
        Continue to Sign In
      </a>
      {% else %}
      <div class="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
        <svg class="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
      </div>
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Verification Failed</h1>
      <p class="text-white/50 text-sm mb-6">The verification link is invalid or has expired. Please try registering again or request a new link.</p>
      <a href="{% url 'accounts:register' %}" class="w-full bg-white/10 text-white font-bold border border-white/20 rounded-xl py-3.5 hover:bg-white/20 active:scale-[0.98] transition-all flex items-center justify-center">
        Return to Register
      </a>
      {% endif %}
    </div>
"""
    }
}

out_dir = "/home/gazy-johnson/Downloads/school/ROOMORA/accounts/templates/accounts"
for filename, data in pages.items():
    content = base_template.replace("{{TITLE}}", data["title"]).replace("{{CONTENT}}", data["content"])
    path = os.path.join(out_dir, filename)
    with open(path, "w") as f:
        f.write(content)
    print(f"Rewrote {filename}")

