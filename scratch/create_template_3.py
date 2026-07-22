import os

template_content = """{% extends "bookings/base_checkout.html" %}
{% load static %}

{% block title %}House Rules & Policy — {{ property.title }}{% endblock %}

{% block content %}
<div class="w-full flex-grow flex flex-col lg:flex-row min-h-[calc(100vh-80px)] bg-white">
  
  <!-- LEFT PANEL: Visuals & Property/Room Info (Sticky) -->
  <div class="w-full lg:w-[45%] xl:w-[50%] bg-[#F5F5F5] lg:sticky lg:top-[80px] lg:h-[calc(100vh-80px)] flex flex-col relative overflow-hidden border-r border-black/5">
    
    <!-- Room Gallery Gallery -->
    <div class="h-64 sm:h-80 lg:h-[55%] w-full relative">
      {% if room and room.images.all %}
        <div class="w-full h-full flex overflow-x-auto snap-x snap-mandatory scrollbar-hide">
          {% for img in room.images.all %}
            <div class="w-full h-full shrink-0 snap-center relative">
              <img src="{{ img.image_url }}" alt="Room Image" class="w-full h-full object-cover">
              <!-- Overlay gradient for text readability -->
              <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
            </div>
          {% endfor %}
        </div>
      {% elif property.main_image %}
        <div class="w-full h-full relative">
          <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-full object-cover">
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
        </div>
      {% else %}
        <div class="w-full h-full flex items-center justify-center bg-[#E5E5E5] text-[#111111]/30 font-medium">
          No Images Available
        </div>
      {% endif %}

      <!-- Room Badge overlay -->
      {% if room %}
        <div class="absolute top-5 left-5 bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-md text-[10px] uppercase tracking-widest font-extrabold text-[#111111] shadow-sm">
          {{ room.get_gender_restriction_display }} Only
        </div>
      {% endif %}
    </div>

    <!-- Booking Summary Details -->
    <div class="flex-grow p-8 sm:p-10 lg:p-12 lg:overflow-y-auto">
      <div class="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-2">{{ property.get_property_type_display }}</div>
      <h2 class="text-3xl font-extrabold text-[#111111] leading-tight mb-2">{{ property.title }}</h2>
      <div class="text-[14px] font-medium text-[#111111]/60 flex items-center gap-1.5 mb-8">
        <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        {{ property.city }}{% if property.region %}, {{ property.region }}{% endif %}
      </div>

      {% if room %}
      <div class="bg-white rounded-2xl p-6 border border-black/5 shadow-sm">
        <div class="flex justify-between items-start mb-4">
          <div>
            <h3 class="font-extrabold text-[#111111] text-[18px]">{{ room.room_number|default:"Standard Room" }}</h3>
            <div class="text-[13px] font-medium text-[#111111]/60 mt-1">{{ room.room_type.name }}</div>
          </div>
          {% if room.status == 'AVAILABLE' %}
            <span class="inline-flex items-center gap-1.5 text-[12px] font-extrabold text-[#059669] bg-[#ECFDF5] px-2.5 py-1 rounded-md">
              <span class="w-1.5 h-1.5 rounded-full bg-[#10B981]"></span> Available
            </span>
          {% elif room.status == 'PARTIALLY_OCCUPIED' %}
            <span class="inline-flex items-center gap-1.5 text-[12px] font-extrabold text-[#D97706] bg-[#FFFBEB] px-2.5 py-1 rounded-md">
              <span class="w-1.5 h-1.5 rounded-full bg-[#F59E0B]"></span> Partially Occupied
            </span>
          {% endif %}
        </div>
        
        <div class="grid grid-cols-2 gap-3 mt-2">
          <div class="flex items-center gap-2 text-[13px] text-[#111111]/70 font-medium">
            <svg class="text-[#111111]/40" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            Max {{ room.total_slots }} occupant{{ room.total_slots|pluralize }}
          </div>
          <div class="flex items-center gap-2 text-[13px] text-[#111111]/70 font-medium">
            <svg class="text-[#111111]/40" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="4" rx="1" ry="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 4.14 12 2l4.5 2.14"/></svg>
            {{ room.get_bed_type_display|default:"Standard Bed" }}
          </div>
        </div>
      </div>
      {% endif %}

      <div class="mt-8 flex items-start gap-3">
        <svg class="shrink-0 text-[#111111]/40 mt-1" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
        <p class="text-[13px] leading-relaxed text-[#111111]/50 font-medium">Your selection is secure. A temporary reservation hold will be applied when you proceed.</p>
      </div>
    </div>
  </div>

  <!-- RIGHT PANEL: Rules & Actions (Scrollable) -->
  <div class="w-full lg:w-[55%] xl:w-[50%] p-6 sm:p-10 lg:p-16 flex flex-col justify-center max-w-3xl mx-auto">
    
    <div class="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-6 w-fit">
      Step 1 of 4
    </div>
    
    <h1 class="text-4xl font-extrabold tracking-tight text-[#111111] mb-2">Review house rules</h1>
    <p class="text-[16px] leading-relaxed text-[#111111]/60 mb-10">Please review the rules set by the host before securing your reservation.</p>

    <!-- Rules Container -->
    <div class="space-y-10">
      
      <!-- Expectations -->
      <div>
        <h3 class="text-xl font-extrabold text-[#111111] mb-5">Property expectations</h3>
        <div class="bg-white border border-black/5 rounded-2xl p-6 shadow-sm">
          {% if property.house_rules %}
            <ul class="space-y-4">
              {% for rule in property.house_rules.splitlines %}
                {% if rule.strip %}
                  <li class="flex items-start gap-3">
                    <svg class="mt-0.5 shrink-0 text-[#111111]" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    <span class="text-[15px] font-medium leading-relaxed text-[#111111]/80">{{ rule.strip }}</span>
                  </li>
                {% endif %}
              {% endfor %}
            </ul>
          {% else %}
            <div class="flex items-start gap-3">
              <svg class="mt-0.5 shrink-0 text-[#111111]" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              <span class="text-[15px] font-medium leading-relaxed text-[#111111]/80">Standard community guidelines and respectful behavior apply during your stay.</span>
            </div>
          {% endif %}
        </div>
      </div>

      <!-- Prohibited -->
      <div>
        <h3 class="text-xl font-extrabold text-[#92400E] mb-5">Prohibited items</h3>
        <div class="bg-[#FFFBEB] border border-[#FDE68A] rounded-2xl p-6">
          <p class="text-[15px] font-medium leading-relaxed text-[#92400E]">
            {% if property.prohibited_items %}
              {{ property.prohibited_items }}
            {% else %}
              Please review the property listing for any restricted items before arrival.
            {% endif %}
          </p>
        </div>
      </div>

    </div>

    <!-- Form -->
    <form method="post" action="{% url 'bookings:acknowledge_house_rules' %}" class="mt-12">
      {% csrf_token %}
      <input type="hidden" name="property_id" value="{{ property.id }}">
      {% if room_id %}<input type="hidden" name="room_id" value="{{ room_id }}">{% endif %}
      {% if unit_type_id %}<input type="hidden" name="unit_type_id" value="{{ unit_type_id }}">{% endif %}

      <label class="block cursor-pointer group mb-10">
        <div class="bg-white rounded-2xl border-2 border-black/5 p-6 transition-all duration-300 hover:border-black/15 group-has-[:checked]:border-[#111111] group-has-[:checked]:bg-[#111111]/5">
          <div class="flex items-center gap-4">
            <input type="checkbox" id="ackCheckbox" name="rules_acknowledged" value="yes" required class="h-6 w-6 shrink-0 rounded border-black/20 text-[#111111] focus:ring-[#111111] transition duration-200">
            <span class="text-[15px] leading-relaxed text-[#111111] font-bold select-none">
              I have read and understood the house rules and policies. I agree to comply with them during my stay.
            </span>
          </div>
        </div>
      </label>

      <div class="flex items-center justify-between pt-6 border-t border-black/5">
        <a href="{% url 'landing:property_detail' property.id %}" class="text-[15px] font-extrabold text-[#111111]/40 transition-colors hover:text-[#111111] underline underline-offset-4">Cancel</a>
        <button type="submit" id="ackSubmitBtn" disabled class="ds-btn w-auto disabled:opacity-30 disabled:cursor-not-allowed px-10 py-4 bg-[#111111] text-white rounded-xl font-extrabold text-[15px] transition-all hover:bg-[#333333] shadow-md">
          Agree & Continue
        </button>
      </div>
    </form>

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
      btn.disabled = !cb.checked;
    }
  });
</script>
<style>
/* Hide scrollbar for gallery */
.scrollbar-hide::-webkit-scrollbar { display: none; }
.scrollbar-hide { -ms-overflow-style: none; scrollbar-width: none; }
</style>
{% endblock %}
"""

with open('/home/gazy-johnson/Downloads/school/ROOMORA/bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(template_content)

print("Redesign template 3 created and applied!")
