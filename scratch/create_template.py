import os

template_content = """{% extends "bookings/base_checkout.html" %}
{% load static %}

{% block title %}Acknowledge House Rules — {{ property.title }}{% endblock %}

{% block content %}
<div class="px-4 py-8 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
  <div class="flex flex-col lg:flex-row gap-8 xl:gap-12 items-start">
    
    <!-- LEFT COLUMN: Action Area -->
    <div class="w-full lg:w-[55%] xl:w-[60%] flex flex-col gap-8">
      
      <!-- Header -->
      <div>
        <div class="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-4">
          Step 1 of 4
        </div>
        <h1 class="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#111111]">Review house rules</h1>
        <p class="mt-3 text-[15px] font-medium leading-relaxed text-[#111111]/50">Please review the host's expectations before you continue to secure this room.</p>
      </div>

      <!-- House Rules Section -->
      <div class="bg-white rounded-[32px] border border-black/5 p-6 sm:p-8 shadow-[0_4px_24px_rgba(0,0,0,0.02)]">
        <div class="flex items-center gap-3 mb-6">
          <div class="flex h-10 w-10 items-center justify-center rounded-[14px] bg-[#111111]/5 text-[#111111]">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
          </div>
          <div>
            <h2 class="text-lg font-extrabold text-[#111111]">Property expectations</h2>
          </div>
        </div>

        <div class="bg-[#F5F5F5] rounded-[24px] p-5 sm:p-6 border border-black/5">
          {% if property.house_rules %}
            <ul class="space-y-4">
              {% for rule in property.house_rules.splitlines %}
                {% if rule.strip %}
                  <li class="flex items-start gap-3">
                    <svg class="mt-1 shrink-0 text-[#111111]/40" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    <span class="text-[14px] sm:text-[15px] font-medium leading-relaxed text-[#111111]/80">{{ rule.strip }}</span>
                  </li>
                {% endif %}
              {% endfor %}
            </ul>
          {% else %}
            <div class="flex items-start gap-3">
              <svg class="mt-1 shrink-0 text-[#111111]/40" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              <span class="text-[14px] sm:text-[15px] font-medium leading-relaxed text-[#111111]/80">Standard community guidelines and respectful behavior apply during your stay.</span>
            </div>
          {% endif %}
        </div>
      </div>

      <!-- Prohibited Items Section -->
      <div class="bg-[#FFFAF0] rounded-[32px] border border-[#FBE3B8] p-6 sm:p-8">
        <div class="flex items-center gap-3 mb-4">
          <div class="flex h-10 w-10 items-center justify-center rounded-[14px] bg-[#FBE3B8]/50 text-[#D97706]">
            <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>
          </div>
          <h2 class="text-lg font-extrabold text-[#92400E]">Prohibited items</h2>
        </div>
        <p class="text-[14px] sm:text-[15px] font-medium leading-relaxed text-[#92400E]/90">
          {% if property.prohibited_items %}
            {{ property.prohibited_items }}
          {% else %}
            Please review the property listing for any restricted items before arrival.
          {% endif %}
        </p>
      </div>

      <!-- Acknowledgment & Actions -->
      <form method="post" action="{% url 'bookings:acknowledge_house_rules' %}" class="space-y-6 mt-2 pb-12">
        {% csrf_token %}
        <input type="hidden" name="property_id" value="{{ property.id }}">
        {% if room_id %}<input type="hidden" name="room_id" value="{{ room_id }}">{% endif %}
        {% if unit_type_id %}<input type="hidden" name="unit_type_id" value="{{ unit_type_id }}">{% endif %}

        <label class="block cursor-pointer group">
          <div id="ackBox" class="bg-white rounded-[24px] border-2 border-black/5 p-5 sm:p-6 transition-all duration-300 hover:border-black/10 group-has-[:checked]:border-[#111111] group-has-[:checked]:bg-[#111111]/5">
            <div class="flex items-start gap-4">
              <input type="checkbox" id="ackCheckbox" name="rules_acknowledged" value="yes" required class="mt-1 h-5 w-5 shrink-0 rounded-[6px] border-black/20 text-[#111111] focus:ring-[#111111] transition duration-200">
              <span class="text-[14px] sm:text-[15px] leading-relaxed text-[#111111] font-semibold select-none">
                I have read and understood the house rules and policies for this property. I agree to comply with them during my stay.
              </span>
            </div>
          </div>
        </label>

        <div class="flex flex-col-reverse sm:flex-row sm:items-center justify-between gap-4 pt-6 border-t border-black/5">
          <a href="{% url 'landing:property_detail' property.id %}" class="text-[14px] font-extrabold text-[#111111]/40 transition-colors hover:text-[#111111] text-center sm:text-left">Cancel booking</a>
          <button type="submit" id="ackSubmitBtn" disabled class="ds-btn sm:w-auto disabled:opacity-30 disabled:cursor-not-allowed px-10 py-4 bg-[#111111] text-white rounded-[18px] font-extrabold transition-all hover:bg-[#333333] shadow-[0_8px_24px_rgba(0,0,0,0.12)]">
            Agree & Continue
          </button>
        </div>
      </form>
    </div>

    <!-- RIGHT COLUMN: Sticky Booking Summary -->
    <div class="w-full lg:w-[45%] xl:w-[40%] lg:sticky lg:top-28 mt-8 lg:mt-0">
      <div class="bg-white rounded-[32px] border border-black/5 overflow-hidden shadow-[0_24px_60px_rgb(0,0,0,0.04)]">
        <!-- Room Image -->
        <div class="aspect-[4/3] w-full bg-[#F5F5F5] relative">
          {% if room %}
            {% with first_img=room.images.all|first %}
              {% if first_img %}
                <img src="{{ first_img.image_url }}" alt="Room Image" class="w-full h-full object-cover">
              {% elif property.main_image %}
                <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-full object-cover">
              {% else %}
                <div class="w-full h-full flex items-center justify-center text-[#111111]/30 font-medium">No Image Available</div>
              {% endif %}
            {% endwith %}
          {% elif property.main_image %}
            <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-full object-cover">
          {% else %}
            <div class="w-full h-full flex items-center justify-center text-[#111111]/30 font-medium">No Image Available</div>
          {% endif %}
          
          {% if room %}
            <div class="absolute top-5 left-5 bg-white/95 backdrop-blur-md px-4 py-2 rounded-full text-[11px] uppercase tracking-widest font-extrabold text-[#111111] shadow-[0_4px_12px_rgb(0,0,0,0.08)]">
              {{ room.get_gender_restriction_display }} Only
            </div>
          {% endif %}
        </div>
        
        <!-- Summary Details -->
        <div class="p-8 sm:p-10 flex flex-col gap-6">
          <div>
            <div class="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-2">{{ property.get_property_type_display }}</div>
            <h3 class="text-2xl font-extrabold text-[#111111] leading-tight tracking-tight">{{ property.title }}</h3>
            <div class="text-[14px] font-medium text-[#111111]/60 mt-2 flex items-center gap-2">
              <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              {{ property.city }}{% if property.region %}, {{ property.region }}{% endif %}
            </div>
          </div>
          
          <div class="h-px w-full bg-black/5"></div>
          
          {% if room %}
          <div>
            <h4 class="font-extrabold text-[#111111] text-[18px] tracking-tight">{{ room.room_number|default:"Standard Room" }}</h4>
            <div class="text-[14px] font-medium text-[#111111]/60 mt-1">{{ room.room_type.name }}</div>
          </div>
          
          <div class="flex flex-wrap gap-2 mt-1">
            <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] border border-black/5 rounded-[10px] px-3 py-1.5 text-[12px] font-extrabold text-[#111111]/70">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              Max {{ room.total_slots }} occupant{{ room.total_slots|pluralize }}
            </span>
            <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] border border-black/5 rounded-[10px] px-3 py-1.5 text-[12px] font-extrabold text-[#111111]/70">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="4" rx="1" ry="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 4.14 12 2l4.5 2.14"/></svg>
              {{ room.get_bed_type_display|default:"Standard Bed" }}
            </span>
            {% if room.private_washroom %}
            <span class="inline-flex items-center gap-1.5 bg-[#ECFDF5] border border-[#A7F3D0] rounded-[10px] px-3 py-1.5 text-[12px] font-extrabold text-[#047857]">
              <svg width="12" height="12" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
              En-suite
            </span>
            {% endif %}
          </div>
          
          <div class="h-px w-full bg-black/5 my-2"></div>
          
          <div class="flex items-center justify-between">
            <span class="text-[13px] font-extrabold text-[#111111]/50 uppercase tracking-wider">Status</span>
            {% if room.status == 'AVAILABLE' %}
              <span class="inline-flex items-center gap-2 text-[14px] font-extrabold text-[#059669]">
                <span class="w-2.5 h-2.5 rounded-full bg-[#10B981] shadow-[0_0_8px_rgba(16,185,129,0.4)]"></span> Available
              </span>
            {% elif room.status == 'PARTIALLY_OCCUPIED' %}
              <span class="inline-flex items-center gap-2 text-[14px] font-extrabold text-[#D97706]">
                <span class="w-2.5 h-2.5 rounded-full bg-[#F59E0B] shadow-[0_0_8px_rgba(245,158,11,0.4)]"></span> Partially Occupied
              </span>
            {% else %}
              <span class="inline-flex items-center gap-2 text-[14px] font-extrabold text-[#111111]/40">
                <span class="w-2.5 h-2.5 rounded-full bg-[#111111]/20"></span> {{ room.get_status_display }}
              </span>
            {% endif %}
          </div>
          {% endif %}
          
        </div>
      </div>
      
      <!-- Trust Banner -->
      <div class="mt-6 flex items-start gap-3 px-2">
        <svg class="shrink-0 text-[#10B981] mt-0.5" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        <p class="text-[13px] leading-relaxed text-[#111111]/50 font-semibold">Your room is protected. Once you proceed, a temporary reservation hold will be placed to guarantee availability while you complete your booking.</p>
      </div>
    </div>
    
  </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const cb = document.getElementById('ackCheckbox');
    const btn = document.getElementById('ackSubmitBtn');
    if(cb && btn) {
      cb.addEventListener('change', function() {
        btn.disabled = !this.checked;
      });
      // Initial check on load (e.g. for back button)
      btn.disabled = !cb.checked;
    }
  });
</script>
{% endblock %}
"""

with open('/home/gazy-johnson/Downloads/school/ROOMORA/bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(template_content)

print("Redesign template created and applied!")
