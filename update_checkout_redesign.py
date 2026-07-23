html_content = """{% extends "bookings/base_checkout.html" %}
{% load static %}

{% block title %}Review & Rules — {{ property.title }}{% endblock %}

{% block content %}
<form method="post" action="{% url 'bookings:acknowledge_house_rules' %}" class="w-full relative">
  {% csrf_token %}
  <input type="hidden" name="property_id" value="{{ property.id }}">
  {% if room_id %}<input type="hidden" name="room_id" value="{{ room_id }}">{% endif %}
  {% if unit_type_id %}<input type="hidden" name="unit_type_id" value="{{ unit_type_id }}">{% endif %}

  <!-- Decorative Background Blur -->
  <div class="absolute top-0 inset-x-0 h-96 bg-gradient-to-b from-[#111111]/5 to-transparent -z-10 pointer-events-none"></div>

  <div class="px-4 py-12 sm:px-6 lg:px-12 max-w-[1400px] mx-auto w-full">
    
    <!-- Header Area -->
    <div class="mb-12">
      <div class="inline-flex items-center gap-2 rounded-full border border-black/10 bg-white/60 backdrop-blur-md px-4 py-1.5 text-[11px] font-extrabold uppercase tracking-[0.2em] text-[#111111]/60 mb-5 shadow-sm">
        <span class="w-2 h-2 rounded-full bg-[#111111] animate-pulse"></span> Step 1 of 4
      </div>
      <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight text-[#111111] leading-tight">Review your selection</h1>
      <p class="mt-4 text-[17px] font-medium leading-relaxed text-[#111111]/60 max-w-2xl">Take a moment to confirm the property details, amenities, and host expectations before securing your room.</p>
    </div>

    <div class="flex flex-col-reverse lg:flex-row gap-10 xl:gap-16 items-start">
      
      <!-- LEFT COLUMN: Details & Rules -->
      <div class="w-full lg:w-[65%] flex flex-col gap-10 pb-20">
        
        <!-- About the Property (Hero Card) -->
        <section class="group">
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 sm:p-10 shadow-[0_8px_30px_rgba(0,0,0,0.04)] transition-all duration-300 hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] relative overflow-hidden">
            <!-- Decorative Accent -->
            <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-gray-100 to-transparent rounded-bl-full opacity-50 -z-10 transition-transform duration-500 group-hover:scale-110"></div>
            
            <div class="flex flex-col sm:flex-row justify-between sm:items-start gap-6 mb-8">
              <div>
                <div class="inline-flex items-center gap-2 text-[12px] font-extrabold text-[#111111]/50 uppercase tracking-widest mb-3">
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>
                  {{ property.get_property_type_display }}
                </div>
                <h2 class="text-3xl sm:text-4xl font-extrabold text-[#111111] tracking-tight">{{ property.title }}</h2>
              </div>
              {% if property.is_verified %}
                <div class="inline-flex items-center gap-2 bg-[#ECFDF5] text-[#059669] px-4 py-2 rounded-full text-[13px] font-extrabold shadow-sm ring-1 ring-[#059669]/20">
                  <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg> Verified Property
                </div>
              {% endif %}
            </div>
            
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-6 mb-8 py-6 border-y border-black/5">
              <div>
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">Total Rooms</div>
                <div class="text-[16px] font-bold text-[#111111]">{{ property.number_of_rooms|default:"10+" }}</div>
              </div>
              <div>
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">Gender</div>
                <div class="text-[16px] font-bold text-[#111111]">{{ property.get_hostel_type_display|default:"Mixed" }}</div>
              </div>
              <div>
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">Rating</div>
                <div class="text-[16px] font-bold text-[#111111]">⭐ {{ property.average_rating|default:"4.5"|floatformat:1 }}/5</div>
              </div>
              <div>
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">Area</div>
                <div class="text-[16px] font-bold text-[#111111]">{{ property.total_area|default:"—" }} m²</div>
              </div>
            </div>
            
            <p class="text-[16px] font-medium leading-relaxed text-[#111111]/70">
              {{ property.description|default:"A premium student accommodation property providing comfort and convenience." }}
            </p>
          </div>
        </section>

        <!-- Bento Grid: Location & Safety -->
        <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          <!-- Location Bento -->
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-300 flex flex-col justify-between">
            <div>
              <div class="w-12 h-12 rounded-[16px] bg-[#111111]/5 flex items-center justify-center text-[#111111] mb-6">
                <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              </div>
              <h3 class="text-xl font-extrabold text-[#111111] mb-2">Location</h3>
              <div class="text-[16px] font-medium text-[#111111]/80 leading-snug">{{ property.address }}</div>
              <div class="text-[14px] font-medium text-[#111111]/50 mt-1">{{ property.city }}{% if property.region %}, {{ property.region }}{% endif %}</div>
            </div>
            
            {% if property.nearest_institution %}
            <div class="mt-6 pt-6 border-t border-black/5">
              <div class="inline-flex items-center gap-2 text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 10v6M2 10l10-5 10 5-10 5z"/><path d="M6 12v5c3 3 9 3 12 0v-5"/></svg>
                Near Campus
              </div>
              <div class="text-[15px] font-bold text-[#111111]/90">{{ property.nearest_institution }}</div>
            </div>
            {% endif %}
          </div>

          <!-- Safety Bento -->
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-300">
            <div class="flex items-center justify-between mb-6">
              <div class="w-12 h-12 rounded-[16px] bg-[#ECFDF5] flex items-center justify-center text-[#059669]">
                <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
              </div>
              {% if property.safety_score %}
                <div class="flex flex-col items-end">
                  <div class="text-[22px] font-extrabold text-[#059669]">{{ property.safety_score }}/10</div>
                  <div class="text-[11px] font-bold uppercase tracking-wider text-[#059669]/60">Safety Score</div>
                </div>
              {% endif %}
            </div>
            <h3 class="text-xl font-extrabold text-[#111111] mb-4">Security & Safety</h3>
            <ul class="space-y-4">
              {% if property.security_personnel %}
                <li class="flex items-center gap-3 text-[15px] font-medium text-[#111111]/70"><svg class="text-[#059669] shrink-0" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> 24/7 Security Personnel</li>
              {% endif %}
              {% if property.cctv %}
                <li class="flex items-center gap-3 text-[15px] font-medium text-[#111111]/70"><svg class="text-[#059669] shrink-0" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> CCTV Surveillance</li>
              {% endif %}
              {% if property.gated_community %}
                <li class="flex items-center gap-3 text-[15px] font-medium text-[#111111]/70"><svg class="text-[#059669] shrink-0" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Gated Community</li>
              {% endif %}
              {% if property.fire_safety_compliance %}
                <li class="flex items-center gap-3 text-[15px] font-medium text-[#111111]/70"><svg class="text-[#059669] shrink-0" width="18" height="18" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Fire Safety Compliant</li>
              {% endif %}
              {% if not property.security_personnel and not property.cctv and not property.gated_community %}
                <li class="text-[15px] font-medium text-[#111111]/70 bg-[#F9FAFB] p-4 rounded-xl border border-black/5">Standard neighborhood security protocols are observed here.</li>
              {% endif %}
            </ul>
          </div>
        </section>

        <!-- Amenities -->
        <section>
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 sm:p-10 shadow-[0_8px_30px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-300">
            <h3 class="text-2xl font-extrabold text-[#111111] mb-8">What this place offers</h3>
            <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {% if property.water_availability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#3B82F6]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Constant Water</div>
                </div>
              {% endif %}
              {% if property.electricity_stability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#EAB308]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Stable Electricity</div>
                </div>
              {% endif %}
              {% if property.internet_availability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#8B5CF6]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12.55a11 11 0 0 1 14.08 0 M1.42 9a16 16 0 0 1 21.16 0 M8.53 16.11a6 6 0 0 1 6.95 0 M12 20h.01"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Fast Internet</div>
                </div>
              {% endif %}
              
              {% for amenity in property.amenities.all|slice:":6" %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#111111]/70" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="9" y1="3" x2="9" y2="21"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">{{ amenity.name }}</div>
                </div>
              {% endfor %}
            </div>
          </div>
        </section>

        <!-- Rules & Expectations -->
        <section>
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 sm:p-10 shadow-[0_8px_30px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.06)] transition-all duration-300">
            <h3 class="text-2xl font-extrabold text-[#111111] mb-8">Things to know</h3>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-10">
              
              <!-- House Rules List -->
              <div>
                <div class="flex items-center gap-3 mb-5">
                  <div class="w-10 h-10 rounded-full bg-[#111111]/5 flex items-center justify-center text-[#111111]">
                    <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>
                  </div>
                  <h4 class="font-extrabold text-[#111111] text-[18px]">Property Rules</h4>
                </div>
                
                {% if property.house_rules %}
                  <ul class="space-y-5">
                    {% for rule in property.house_rules.splitlines %}
                      {% if rule.strip %}
                        <li class="flex items-start gap-4">
                          <svg class="mt-0.5 shrink-0 text-[#111111]/30" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                          <span class="text-[15px] font-medium leading-relaxed text-[#111111]/80">{{ rule.strip }}</span>
                        </li>
                      {% endif %}
                    {% endfor %}
                  </ul>
                {% else %}
                  <div class="bg-[#F9FAFB] p-5 rounded-[20px] border border-black/5 text-[15px] font-medium text-[#111111]/70">
                    Standard community guidelines and respectful behavior apply during your stay.
                  </div>
                {% endif %}
              </div>
              
              <!-- Additional Policies -->
              <div>
                <div class="flex items-center gap-3 mb-5">
                  <div class="w-10 h-10 rounded-full bg-[#111111]/5 flex items-center justify-center text-[#111111]">
                    <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                  </div>
                  <h4 class="font-extrabold text-[#111111] text-[18px]">Additional Policies</h4>
                </div>

                <div class="flex flex-col gap-4">
                  {% if property.curfew_time %}
                  <div class="bg-[#F9FAFB] p-5 rounded-[20px] border border-black/5 flex justify-between items-center">
                    <div class="font-extrabold text-[15px] text-[#111111]">Curfew</div>
                    <div class="text-[15px] font-bold text-[#111111]/60">{{ property.curfew_time }}</div>
                  </div>
                  {% endif %}
                  
                  {% if property.visitor_policy %}
                  <div class="bg-[#F9FAFB] p-5 rounded-[20px] border border-black/5">
                    <div class="font-extrabold text-[15px] text-[#111111] mb-1">Visitor Policy</div>
                    <div class="text-[14px] font-medium text-[#111111]/70 leading-relaxed">{{ property.visitor_policy }}</div>
                  </div>
                  {% endif %}
                </div>
              </div>
              
            </div>

            <div class="mt-8 pt-8 border-t border-black/5">
              <div class="bg-[#FFFAF0] border border-[#FDE68A] rounded-[24px] p-6 sm:p-8 flex items-start gap-5">
                <div class="w-12 h-12 shrink-0 rounded-full bg-[#FEF3C7] flex items-center justify-center text-[#D97706]">
                  <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                </div>
                <div>
                  <h4 class="font-extrabold text-[#92400E] text-[16px] mb-2">Prohibited Items</h4>
                  <p class="text-[15px] font-medium leading-relaxed text-[#92400E]/90">
                    {% if property.prohibited_items %}
                      {{ property.prohibited_items }}
                    {% else %}
                      Please review the property listing for any restricted items (e.g. hot plates, weapons, illicit substances) before arrival.
                    {% endif %}
                  </p>
                </div>
              </div>
            </div>

          </div>
        </section>
      </div>

      <!-- RIGHT COLUMN: Sticky Summary & Action -->
      <div class="w-full lg:w-[35%] lg:sticky lg:top-[120px] z-10">
        <div class="bg-white/95 backdrop-blur-3xl rounded-[32px] border border-black/10 shadow-[0_24px_50px_rgba(0,0,0,0.06)] overflow-hidden flex flex-col group transition-all duration-300 hover:shadow-[0_32px_60px_rgba(0,0,0,0.08)]">
          
          <!-- Room Images Carousel / Masonry -->
          <div class="p-4 pb-0 relative">
            <div class="flex gap-3 overflow-x-auto pb-4 scrollbar-hide snap-x rounded-[24px] relative">
              {% if room and room.images.exists %}
                {% for r_img in room.images.all %}
                  <div class="shrink-0 snap-center w-full relative">
                    <img src="{{ r_img.image.url }}" alt="{{ r_img.get_image_type_display }}" class="w-full h-[220px] object-cover rounded-[20px] shadow-sm">
                    <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent rounded-[20px] pointer-events-none"></div>
                  </div>
                {% endfor %}
              {% elif property.main_image %}
                <div class="shrink-0 snap-center w-full relative">
                  <img src="{{ property.main_image.url }}" alt="{{ property.title }}" class="w-full h-[220px] object-cover rounded-[20px] shadow-sm">
                  <div class="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent rounded-[20px] pointer-events-none"></div>
                </div>
              {% endif %}
            </div>
            
            {% if room %}
              <div class="absolute bottom-8 left-8 bg-white/90 backdrop-blur-md px-4 py-1.5 rounded-full shadow-lg text-[13px] font-extrabold text-[#111111]">
                {{ room.room_number|default:"Standard Room" }}
              </div>
            {% endif %}
          </div>

          <div class="px-8 py-6 flex flex-col gap-6">
            
            <!-- Room Highlights -->
            {% if room %}
            <div>
              <div class="flex justify-between items-start mb-2">
                <div class="text-[18px] font-extrabold text-[#111111] leading-tight">{{ room.room_type.room_type_name|default:room.room_type.name }}</div>
                <div class="bg-[#111111] text-white px-3 py-1 rounded-full text-[10px] font-extrabold uppercase tracking-widest whitespace-nowrap">{{ room.room_type.get_gender_restriction_display|default:"Mixed" }}</div>
              </div>
              
              <div class="flex flex-wrap gap-2 mt-4">
                <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] rounded-[12px] px-3 py-2 text-[13px] font-bold text-[#111111]/80">
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                  Max {{ room.total_slots }} occupant{{ room.total_slots|pluralize }}
                </span>
                <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] rounded-[12px] px-3 py-2 text-[13px] font-bold text-[#111111]/80">
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><rect x="3" y="8" width="18" height="4" rx="1" ry="1"/><path d="M12 8v13"/><path d="M19 12v7a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2v-7"/><path d="M7.5 4.14 12 2l4.5 2.14"/></svg>
                  {{ room.room_type.get_bed_type_display|default:"Standard Bed" }}
                </span>
                <span class="inline-flex items-center gap-1.5 bg-[#F5F5F5] rounded-[12px] px-3 py-2 text-[13px] font-bold text-[#111111]/80">
                  <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>
                  {{ room.room_type.get_billing_model_display|default:"Semester-Based" }}
                </span>
              </div>
            </div>
            
            <div class="bg-gradient-to-br from-[#F9FAFB] to-[#F3F4F6] rounded-[24px] p-6 border border-black/5 relative overflow-hidden">
              <div class="absolute -right-4 -top-4 w-24 h-24 bg-black/5 rounded-full blur-2xl"></div>
              <div class="text-[12px] font-extrabold uppercase tracking-widest text-[#111111]/40 mb-1 relative z-10">Total Pricing</div>
              {% with room_price=room.room_type.pricing_models.first %}
              {% if room_price %}
                <div class="flex items-baseline gap-1.5 relative z-10">
                  <span class="text-[32px] font-extrabold text-[#111111] tracking-tight">GH&#8373;{% if room_price.semester_price %}{{ room_price.semester_price|floatformat:0 }}{% elif room_price.monthly_price %}{{ room_price.monthly_price|floatformat:0 }}{% elif room_price.yearly_price %}{{ room_price.yearly_price|floatformat:0 }}{% else %}—{% endif %}</span>
                  <span class="text-[14px] font-bold text-[#111111]/50">
                    {% if room_price.semester_price %}/ semester
                    {% elif room_price.monthly_price %}/ month
                    {% elif room_price.yearly_price %}/ year
                    {% endif %}
                  </span>
                </div>
              {% else %}
                <div class="text-[20px] font-extrabold text-[#111111] relative z-10">Price not set</div>
              {% endif %}
              {% endwith %}
            </div>
            {% endif %}

            <div class="h-px w-full bg-gradient-to-r from-transparent via-black/10 to-transparent my-1"></div>

            <!-- Checkbox Action -->
            <label class="block cursor-pointer group mt-2 relative">
              <div class="bg-[#F5F5F5] rounded-[24px] p-5 transition-all duration-300 border-[2.5px] border-transparent group-hover:bg-[#E5E5E5] group-has-[:checked]:border-[#111111] group-has-[:checked]:bg-white shadow-sm relative z-10">
                <div class="flex items-start gap-4">
                  <div class="relative flex items-center justify-center mt-0.5">
                    <input type="checkbox" id="ackCheckbox" name="rules_acknowledged" value="yes" required class="peer h-6 w-6 appearance-none rounded-[8px] border-2 border-[#111111]/20 bg-white checked:border-[#111111] checked:bg-[#111111] focus:ring-0 focus:outline-none transition-all duration-200 cursor-pointer">
                    <svg class="absolute w-3.5 h-3.5 pointer-events-none stroke-white opacity-0 peer-checked:opacity-100 transition-opacity duration-200" fill="none" stroke-width="3.5" viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  </div>
                  <span class="text-[14px] leading-snug text-[#111111]/90 font-bold select-none group-has-[:checked]:text-[#111111] transition-colors">
                    I agree to the property rules, prohibited items, and host policies.
                  </span>
                </div>
              </div>
            </label>

            <!-- Submit Button -->
            <button type="submit" id="ackSubmitBtn" disabled class="relative w-full flex items-center justify-center gap-3 px-8 py-5 bg-[#111111] text-white rounded-[24px] font-extrabold text-[17px] transition-all duration-300 hover:bg-[#222222] hover:-translate-y-1 shadow-[0_16px_32px_rgba(17,17,17,0.2)] disabled:opacity-30 disabled:hover:bg-[#111111] disabled:hover:translate-y-0 disabled:shadow-none disabled:cursor-not-allowed overflow-hidden group">
              <span class="relative z-10">Reserve Room</span>
              <svg class="relative z-10 transition-transform duration-300 group-hover:translate-x-1" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
              <!-- Shimmer effect -->
              <div class="absolute inset-0 -translate-x-full bg-gradient-to-r from-transparent via-white/20 to-transparent group-hover:animate-shimmer pointer-events-none"></div>
            </button>
            
            <div class="text-center mt-2">
              <a href="{% url 'landing:property_detail' property.id %}" class="inline-flex items-center justify-center text-[14px] font-extrabold text-[#111111]/40 hover:text-[#111111] transition-colors gap-2">
                <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
                Go Back
              </a>
            </div>

          </div>
        </div>
      </div>
      
    </div>
  </div>
</form>
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
@keyframes shimmer {
  100% { transform: translateX(100%); }
}
.animate-shimmer {
  animation: shimmer 1.5s infinite;
}
</style>
{% endblock %}
"""
with open('bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(html_content)
