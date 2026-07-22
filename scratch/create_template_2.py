import os

template_content = """{% extends "bookings/base_checkout.html" %}
{% load static %}

{% block title %}House Rules & Policy — {{ property.title }}{% endblock %}

{% block content %}
<div class="px-4 py-12 sm:px-6 lg:px-8 max-w-4xl mx-auto w-full">
  
  <div class="mb-10 text-center">
    <div class="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-4 py-1.5 text-[12px] font-bold uppercase tracking-[0.2em] text-[#111111]/50 mb-6">
      Step 1 of 4
    </div>
    <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#111111]">House Rules & Policy</h1>
    <p class="mt-4 text-[16px] leading-relaxed text-[#111111]/60 max-w-2xl mx-auto">Please review the rules set by the host before securing your reservation.</p>
  </div>

  <!-- Booking Summary Header -->
  <div class="bg-white rounded-[24px] border border-black/5 overflow-hidden shadow-[0_4px_24px_rgba(0,0,0,0.02)] mb-8 flex flex-col sm:flex-row items-stretch">
    <!-- Image -->
    <div class="w-full sm:w-1/3 h-48 sm:h-auto bg-[#F5F5F5] relative shrink-0">
      {% if room and room.images.all %}
        <img src="{{ room.images.all.0.image_url }}" alt="Room Image" class="w-full h-full object-cover">
      {% elif property.main_image %}
        <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-full object-cover">
      {% else %}
        <div class="w-full h-full flex items-center justify-center text-[#111111]/30 text-sm font-medium">No Image Available</div>
      {% endif %}
      
      {% if room %}
        <div class="absolute top-3 left-3 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-full text-[10px] uppercase tracking-widest font-extrabold text-[#111111] shadow-sm">
          {{ room.get_gender_restriction_display }} Only
        </div>
      {% endif %}
    </div>
    
    <!-- Details -->
    <div class="p-6 sm:p-8 flex flex-col justify-center flex-grow">
      <div class="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-1">{{ property.get_property_type_display }}</div>
      <h3 class="text-xl font-extrabold text-[#111111] leading-tight">{{ property.title }}</h3>
      <div class="text-[14px] font-medium text-[#111111]/60 mt-1 mb-4 flex items-center gap-1.5">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        {{ property.city }}{% if property.region %}, {{ property.region }}{% endif %}
      </div>
      
      {% if room %}
      <div class="h-px w-full bg-black/5 mb-4"></div>
      <div class="flex items-center justify-between">
        <div>
          <h4 class="font-bold text-[#111111] text-[16px]">{{ room.room_number|default:"Standard Room" }}</h4>
          <div class="text-[13px] font-medium text-[#111111]/60">{{ room.room_type.name }}</div>
        </div>
        <div class="text-right">
          <div class="text-[11px] font-extrabold text-[#111111]/40 uppercase tracking-wider mb-0.5">Status</div>
          {% if room.status == 'AVAILABLE' %}
            <span class="inline-flex items-center gap-1.5 text-[13px] font-extrabold text-[#059669]">
              <span class="w-2 h-2 rounded-full bg-[#10B981]"></span> Available
            </span>
          {% elif room.status == 'PARTIALLY_OCCUPIED' %}
            <span class="inline-flex items-center gap-1.5 text-[13px] font-extrabold text-[#D97706]">
              <span class="w-2 h-2 rounded-full bg-[#F59E0B]"></span> Partially Occupied
            </span>
          {% endif %}
        </div>
      </div>
      {% endif %}
    </div>
  </div>

  <!-- Rules Section -->
  <div class="bg-white rounded-[24px] border border-black/5 p-8 sm:p-10 shadow-[0_4px_24px_rgba(0,0,0,0.02)] mb-8">
    <h2 class="text-2xl font-extrabold text-[#111111] mb-6">Property expectations</h2>
    
    <div class="bg-[#F5F5F5] rounded-[16px] p-6">
      {% if property.house_rules %}
        <ul class="space-y-4">
          {% for rule in property.house_rules.splitlines %}
            {% if rule.strip %}
              <li class="flex items-start gap-4">
                <svg class="mt-0.5 shrink-0 text-[#111111]/40" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                <span class="text-[15px] font-medium leading-relaxed text-[#111111]/80">{{ rule.strip }}</span>
              </li>
            {% endif %}
          {% endfor %}
        </ul>
      {% else %}
        <div class="flex items-start gap-4">
          <svg class="mt-0.5 shrink-0 text-[#111111]/40" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
          <span class="text-[15px] font-medium leading-relaxed text-[#111111]/80">Standard community guidelines and respectful behavior apply during your stay.</span>
        </div>
      {% endif %}
    </div>

    <h2 class="text-2xl font-extrabold text-[#111111] mt-10 mb-6">Prohibited items</h2>
    <div class="bg-[#FFFAF0] rounded-[16px] p-6 border border-[#FBE3B8]">
      <p class="text-[15px] font-medium leading-relaxed text-[#92400E]">
        {% if property.prohibited_items %}
          {{ property.prohibited_items }}
        {% else %}
          Please review the property listing for any restricted items before arrival.
        {% endif %}
      </p>
    </div>
  </div>

  <!-- Acknowledgment & Form -->
  <form method="post" action="{% url 'bookings:acknowledge_house_rules' %}" class="space-y-6">
    {% csrf_token %}
    <input type="hidden" name="property_id" value="{{ property.id }}">
    {% if room_id %}<input type="hidden" name="room_id" value="{{ room_id }}">{% endif %}
    {% if unit_type_id %}<input type="hidden" name="unit_type_id" value="{{ unit_type_id }}">{% endif %}

    <label class="block cursor-pointer group">
      <div class="bg-white rounded-[20px] border-2 border-black/5 p-6 sm:p-8 transition-all duration-300 hover:border-black/15 group-has-[:checked]:border-[#111111] group-has-[:checked]:bg-[#111111]/5">
        <div class="flex items-center gap-5">
          <input type="checkbox" id="ackCheckbox" name="rules_acknowledged" value="yes" required class="h-6 w-6 shrink-0 rounded-[6px] border-black/20 text-[#111111] focus:ring-[#111111] transition duration-200">
          <span class="text-[16px] leading-relaxed text-[#111111] font-bold select-none">
            I have read and understood the house rules and policies for this property. I agree to comply with them during my stay.
          </span>
        </div>
      </div>
    </label>

    <div class="flex items-center justify-between pt-8 pb-16 border-t border-black/5 mt-8">
      <a href="{% url 'landing:property_detail' property.id %}" class="text-[15px] font-extrabold text-[#111111]/40 transition-colors hover:text-[#111111]">Cancel</a>
      <button type="submit" id="ackSubmitBtn" disabled class="ds-btn w-auto disabled:opacity-30 disabled:cursor-not-allowed px-12 py-4 bg-[#111111] text-white rounded-[16px] font-extrabold text-[16px] transition-all hover:bg-[#333333] shadow-lg">
        Agree & Continue
      </button>
    </div>
  </form>
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
      btn.disabled = !cb.checked;
    }
  });
</script>
{% endblock %}
"""

with open('/home/gazy-johnson/Downloads/school/ROOMORA/bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(template_content)

print("Redesign template 2 created and applied!")
