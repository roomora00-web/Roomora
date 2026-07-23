import os

content = """{% extends "accounts/base_auth.html" %}
{% load static %}

{% block title %}Sign In — Roomora{% endblock %}

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
  input[type="text"],
  select {
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
  input[type="text"]:focus,
  select:focus {
    border-color: rgba(255, 255, 255, 0.3) !important;
    background: rgba(0, 0, 0, 0.4) !important;
  }

  input::placeholder {
    color: rgba(255, 255, 255, 0.3) !important;
  }
  
  input[type="checkbox"] {
    accent-color: #FFFFFF;
    width: 1rem;
    height: 1rem;
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
  
  <div class="glass-card w-full max-w-md rounded-3xl p-8 sm:p-10 shadow-2xl relative z-10">
    
    <!-- Logo -->
    <div class="flex justify-center mb-8">
      <a href="{% url 'landing:home' %}" class="flex items-center gap-3 hover:opacity-80 transition-opacity">
        <div class="h-10 w-10 bg-white rounded-xl flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0A0A0A" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
        </div>
        <span class="text-2xl font-bold tracking-tight text-white">Roomora</span>
      </a>
    </div>

    <div class="text-center mb-8">
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Welcome back</h1>
      <p class="text-white/50 text-sm">Sign in to your account to continue.</p>
    </div>

    {% if messages %}
    <div class="mb-6 space-y-2">
      {% for message in messages %}
      <div class="p-4 rounded-xl text-sm font-medium border {% if message.tags == 'error' %}bg-red-500/10 border-red-500/20 text-red-400{% elif message.tags == 'success' %}bg-green-500/10 border-green-500/20 text-green-400{% else %}bg-blue-500/10 border-blue-500/20 text-blue-400{% endif %}">
        {{ message }}
      </div>
      {% endfor %}
    </div>
    {% endif %}

    <form method="post" action="{% url 'accounts:login' %}" class="space-y-5">
      {% csrf_token %}
      
      <div class="space-y-1.5">
        <label class="block text-sm font-medium text-white/80 pl-1">Email address</label>
        {{ form.email }}
      </div>
      
      <div class="space-y-1.5">
        <div class="flex items-center justify-between pl-1 pr-1">
          <label class="block text-sm font-medium text-white/80">Password</label>
          <a href="{% url 'accounts:forgot-password' %}" class="text-xs font-semibold text-white/60 hover:text-white transition-colors">Forgot password?</a>
        </div>
        <div class="relative">
          {{ form.password }}
        </div>
      </div>
      
      <div class="flex items-center pt-2">
        <label class="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" name="remember_me" class="rounded border-white/20 bg-black/20 text-white focus:ring-white/50">
          <span class="text-sm text-white/60 select-none">Remember for 30 days</span>
        </label>
      </div>
      
      <button type="submit" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-2">
        Sign In
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
      </button>
    </form>
    
    <div class="mt-8 text-center border-t border-white/10 pt-6">
      <p class="text-sm text-white/50">
        Don't have an account? 
        <a href="{% url 'accounts:register' %}" class="text-white font-semibold hover:underline decoration-white/30 underline-offset-4 transition-all">Create one free</a>
      </p>
    </div>

  </div>
</div>

<script>
  // Add styling wrapper around form inputs dynamically if needed
</script>
{% endblock %}
"""

with open('/home/gazy-johnson/Downloads/school/ROOMORA/accounts/templates/accounts/login.html', 'w') as f:
    f.write(content)
