import os

content = """{% extends "accounts/base_auth.html" %}
{% load static %}

{% block title %}Create Account — Roomora{% endblock %}

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
    -webkit-appearance: none;
    -moz-appearance: none;
    appearance: none;
  }
  
  /* Select dropdown arrow fix for custom select */
  select {
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 1rem center !important;
    background-size: 1em !important;
  }
  select option {
    background: #111111;
    color: #FFFFFF;
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
    width: 1.1rem;
    height: 1.1rem;
    margin-top: 0.1rem;
    cursor: pointer;
  }

  .ambient-glow {
    position: fixed;
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
<div class="min-h-screen w-full flex items-center justify-center relative overflow-x-hidden px-4 py-12">
  <div class="ambient-glow"></div>
  
  <div class="glass-card w-full max-w-[600px] rounded-3xl p-6 sm:p-10 shadow-2xl relative z-10 my-auto">
    
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
      <h1 class="text-2xl font-bold text-white mb-2 tracking-tight">Create your account</h1>
      <p class="text-white/50 text-sm">Free forever. Book your first room in minutes.</p>
    </div>

    {% if form.errors %}
    <div class="mb-6 space-y-2 p-4 rounded-xl text-sm font-medium border bg-red-500/10 border-red-500/20 text-red-400">
      <ul class="list-disc pl-5 space-y-1">
        {% for field, errors in form.errors.items %}
          {% for error in errors %}<li>{{ error }}</li>{% endfor %}
        {% endfor %}
        {% for error in form.non_field_errors %}<li>{{ error }}</li>{% endfor %}
      </ul>
    </div>
    {% endif %}

    <form method="post" action="{% url 'accounts:register' %}" class="space-y-6">
      {% csrf_token %}
      
      <!-- Personal Info -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-white/40 uppercase tracking-widest pl-1 border-b border-white/5 pb-2">Personal Info</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">First Name</label>
            {{ form.first_name }}
          </div>
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Last Name</label>
            {{ form.last_name }}
          </div>
        </div>
      </div>

      <!-- Contact -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-white/40 uppercase tracking-widest pl-1 border-b border-white/5 pb-2">Contact</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Email Address</label>
            {{ form.email }}
          </div>
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Phone Number</label>
            {{ form.phone_number }}
          </div>
        </div>
      </div>

      <!-- About You -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-white/40 uppercase tracking-widest pl-1 border-b border-white/5 pb-2">About You</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Gender</label>
            {{ form.gender }}
          </div>
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">I am a...</label>
            {{ form.user_type }}
          </div>
        </div>
      </div>

      <!-- Security -->
      <div class="space-y-4">
        <div class="text-xs font-bold text-white/40 uppercase tracking-widest pl-1 border-b border-white/5 pb-2">Security</div>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Password</label>
            {{ form.password }}
          </div>
          <div class="space-y-1.5">
            <label class="block text-sm font-medium text-white/80 pl-1">Confirm Password</label>
            {{ form.confirm_password }}
          </div>
        </div>
      </div>
      
      <!-- Terms -->
      <div class="pt-4">
        <label class="flex items-start gap-3 cursor-pointer p-3 rounded-xl border border-white/5 bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
          {{ form.agree_terms }}
          <span class="text-sm text-white/60 leading-relaxed -mt-0.5">
            I agree to the <a href="#" class="text-white hover:underline underline-offset-2">Terms of Service</a> and <a href="#" class="text-white hover:underline underline-offset-2">Privacy Policy</a>. I confirm I am a student or landlord.
          </span>
        </label>
      </div>
      
      <button type="submit" class="w-full bg-white text-[#0A0A0A] font-bold rounded-xl py-3.5 hover:bg-white/90 active:scale-[0.98] transition-all flex items-center justify-center gap-2 mt-4 shadow-lg shadow-white/5">
        Create Account
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
      </button>
    </form>
    
    <div class="mt-8 text-center border-t border-white/10 pt-6">
      <p class="text-sm text-white/50">
        Already have an account? 
        <a href="{% url 'accounts:login' %}" class="text-white font-semibold hover:underline decoration-white/30 underline-offset-4 transition-all">Sign in here</a>
      </p>
    </div>

  </div>
</div>
{% endblock %}
"""

with open('/home/gazy-johnson/Downloads/school/ROOMORA/accounts/templates/accounts/register.html', 'w') as f:
    f.write(content)
