import os

template_content = """{% extends "bookings/base_checkout.html" %}
{% load static %}

{% block title %}House Rules & Policy — {{ property.title }}{% endblock %}

{% block content %}
<div class="px-4 py-12 sm:px-6 lg:px-8 max-w-6xl mx-auto w-full">
  
  <div class="mb-12">
    <div class="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white px-3 py-1 text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/50 mb-4">
      Step 1 of 4
    </div>
    <h1 class="text-4xl sm:text-[44px] font-extrabold tracking-tight text-[#111111] leading-tight">Review house rules</h1>
    <p class="mt-3 text-[16px] leading-relaxed text-[#111111]/60">Please review the rules set by the host before securing your reservation.</p>
  </div>

  <div class="flex flex-col-reverse lg:flex-row gap-12 xl:gap-16 items-start">
    
    <!-- LEFT COLUMN: Rules & Form (Action Area) -->
    <div class="w-full lg:w-[55%] flex flex-col gap-10">
      
      <!-- Expectations -->
      <div>
        <h3 class="text-xl font-extrabold text-[#111111] mb-5">Property expectations</h3>
        <div class="bg-white border border-black/5 rounded-[24px] p-6 sm:p-8 shadow-sm">
          {% if property.house_rules %}
            <ul class="space-y-5">
              {% for rule in property.house_rules.splitlines %}
                {% if rule.strip %}
                  <li class="flex items-start gap-4">
                    <svg class="mt-0.5 shrink-0 text-[#111111]/40" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                    <span class="text-[15px] sm:text-[16px] font-medium leading-relaxed text-[#111111]/80">{{ rule.strip }}</span>
                  </li>
                {% endif %}
              {% endfor %}
            </ul>
          {% else %}
            <div class="flex items-start gap-4">
              <svg class="mt-0.5 shrink-0 text-[#111111]/40" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
              <span class="text-[15px] sm:text-[16px] font-medium leading-relaxed text-[#111111]/80">Standard community guidelines and respectful behavior apply during your stay.</span>
            </div>
          {% endif %}
        </div>
      </div>

      <!-- Prohibited Items -->
      <div>
        <h3 class="text-xl font-extrabold text-[#92400E] mb-5">Prohibited items</h3>
        <div class="bg-[#FFFAF0] border border-[#FDE68A] rounded-[24px] p-6 sm:p-8">
          <p class="text-[15px] sm:text-[16px] font-medium leading-relaxed text-[#92400E]">
            {% if property.prohibited_items %}
              {{ property.prohibited_items }}
            {% else %}
              Please review the property listing for any restricted items before arrival.
            {% endif %}
          </p>
        </div>
      </div>

      <!-- Form -->
      <form method="post" action="{% url 'bookings:acknowledge_house_rules' %}" class="mt-4">
        {% csrf_token %}
        <input type="hidden" name="property_id" value="{{ property.id }}">
        {% if room_id %}<input type="hidden" name="room_id" value="{{ room_id }}">{% endif %}
        {% if unit_type_id %}<input type="hidden" name="unit_type_id" value="{{ unit_type_id }}">{% endif %}

        <label class="block cursor-pointer group mb-10">
          <div class="bg-white rounded-[24px] border-2 border-black/5 p-6 sm:p-8 transition-all duration-300 hover:border-black/15 group-has-[:checked]:border-[#111111] group-has-[:checked]:bg-[#111111]/5 shadow-sm">
            <div class="flex items-center gap-5">
              <input type="checkbox" id="ackCheckbox" name="rules_acknowledged" value="yes" required class="h-6 w-6 shrink-0 rounded-[6px] border-black/20 text-[#111111] focus:ring-[#111111] transition duration-200">
              <span class="text-[15px] sm:text-[16px] leading-relaxed text-[#111111] font-bold select-none">
                I have read and understood the house rules and policies. I agree to comply with them during my stay.
              </span>
            </div>
          </div>
        </label>

        <div class="flex flex-col-reverse sm:flex-row items-center justify-between gap-4 pt-8 border-t border-black/5">
          <a href="{% url 'landing:property_detail' property.id %}" class="text-[15px] font-extrabold text-[#111111]/40 transition-colors hover:text-[#111111] underline underline-offset-4 w-full sm:w-auto text-center">Cancel</a>
          <button type="submit" id="ackSubmitBtn" disabled class="ds-btn w-full sm:w-auto disabled:opacity-30 disabled:cursor-not-allowed px-12 py-4 bg-[#111111] text-white rounded-[16px] font-extrabold text-[16px] transition-all hover:bg-[#333333] shadow-[0_8px_24px_rgba(0,0,0,0.12)]">
            Agree & Continue
          </button>
        </div>
      </form>

    </div>

    <!-- RIGHT COLUMN: Booking Summary (Sticky Sidebar) -->
    <div class="w-full lg:w-[45%] lg:sticky lg:top-[120px]">
      <div class="bg-white rounded-[32px] border border-black/5 overflow-hidden shadow-[0_12px_40px_rgba(0,0,0,0.04)]">
        
        <div class="p-8 sm:p-10 flex flex-col gap-6">
          <!-- Room Images Mini Gallery (Like property details page) -->
          <div class="flex gap-3 overflow-x-auto pb-2 scrollbar-hide snap-x">
            {% if room and room.images.exists %}
              {% for r_img in room.images.all %}
                <div class="shrink-0 snap-start">
                  <img src="{{ r_img.image.url }}" alt="{{ r_img.get_image_type_display }}" class="w-[140px] h-[100px] object-cover rounded-[16px] shadow-sm border border-black/5">
                </div>
              {% endfor %}
            {% elif property.main_image %}
              <div class="shrink-0 snap-start">
                <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-[180px] object-cover rounded-[16px] shadow-sm border border-black/5">
              </div>
            {% else %}
              <div class="w-full h-[120px] flex items-center justify-center bg-[#F5F5F5] rounded-[16px] text-[#111111]/30 font-medium text-sm">
                No Images Available
              </div>
            {% endif %}
          </div>
          
          <div class="mt-2">
            <div class="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/40 mb-2">{{ property.get_property_type_display }}</div>
            <h3 class="text-2xl sm:text-3xl font-extrabold text-[#111111] leading-tight tracking-tight">{{ property.title }}</h3>
            <div class="text-[14px] font-medium text-[#111111]/60 mt-3 flex items-center gap-2">
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
            <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] border border-black/5 rounded-[12px] px-3.5 py-2 text-[12px] font-extrabold text-[#111111]/70">
              <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              Max {{ room.total_slots }} occupant{{ room.total_slots|pluralize }}
            </span>
            <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] border border-black/5 rounded-[12px] px-3.5 py-2 text-[12px] font-extrabold text-[#111111]/70">
              <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="4" rx="1" ry="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 4.14 12 2l4.5 2.14"/></svg>
              {{ room.get_bed_type_display|default:"Standard Bed" }}
            </span>
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
            {% endif %}
          </div>
          {% endif %}
          
        </div>
      </div>
      
      <!-- Trust Banner -->
      <div class="mt-6 flex items-start gap-4 px-2">
        <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#ECFDF5] text-[#10B981]">
          <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <p class="text-[13.5px] leading-relaxed text-[#111111]/60 font-semibold mt-1">Your selection is secure. A temporary reservation hold will be applied when you proceed to the next step.</p>
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

print("Redesign template 4 created and applied!")
