with open('bookings/templates/bookings/house_rules_acknowledgment.html', 'r') as f:
    content = f.read()

# 1. Add Proximity to Location
loc_target = """<div class="text-[14px] font-medium text-[#111111]/50 mt-1">{{ property.city }}{% if property.region %}, {{ property.region }}{% endif %}</div>"""
loc_replacement = loc_target + """
              {% if property.nearest_institution %}
              <div class="mt-4 pt-4 border-t border-black/5">
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-1">Near Campus</div>
                <div class="text-[14px] font-bold text-[#111111]/80">{{ property.nearest_institution }}</div>
              </div>
              {% endif %}"""
content = content.replace(loc_target, loc_replacement)

# 2. Add Curfew and Visitor Policies
rules_target = """{% else %}
              <p class="text-[15px] font-medium text-[#111111]/70">Standard community guidelines and respectful behavior apply during your stay.</p>
            {% endif %}
          </div>"""
rules_replacement = rules_target + """
          {% if property.visitor_policy or property.curfew_time %}
          <div class="bg-white border border-black/5 rounded-[24px] p-6 sm:p-8 shadow-sm mb-6">
            <h4 class="font-extrabold text-[#111111] text-[16px] mb-4">Additional Policies</h4>
            <div class="flex flex-col gap-4">
              {% if property.curfew_time %}
              <div class="flex gap-4 items-start">
                <div class="mt-0.5 bg-[#111111]/5 p-2 rounded-[10px] text-[#111111]">
                  <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
                </div>
                <div>
                  <div class="font-bold text-[14px] text-[#111111]">Curfew</div>
                  <div class="text-[14px] font-medium text-[#111111]/70">{{ property.curfew_time }}</div>
                </div>
              </div>
              {% endif %}
              
              {% if property.visitor_policy %}
              <div class="flex gap-4 items-start">
                <div class="mt-0.5 bg-[#111111]/5 p-2 rounded-[10px] text-[#111111]">
                  <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <div>
                  <div class="font-bold text-[14px] text-[#111111]">Visitor Policy</div>
                  <div class="text-[14px] font-medium text-[#111111]/70">{{ property.visitor_policy }}</div>
                </div>
              </div>
              {% endif %}
            </div>
          </div>
          {% endif %}"""
content = content.replace(rules_target, rules_replacement)

# 3. Add Pricing to Right Sidebar
room_target = """</div>
            </div>
            {% endif %}

            <div class="h-px w-full bg-black/5 my-1"></div>"""
room_replacement = """</div>
            </div>
            
            <div class="mt-2 bg-[#F9FAFB] rounded-[16px] p-4 border border-black/5">
              <div class="text-[12px] font-bold uppercase tracking-wider text-[#111111]/50 mb-1">Pricing</div>
              {% with room_price=room.room_type.pricing_models.first %}
              {% if room_price %}
                <div class="flex items-baseline gap-1">
                  <span class="text-[24px] font-extrabold text-[#111111]">GH&#8373; {% if room_price.semester_price %}{{ room_price.semester_price|floatformat:0 }}{% elif room_price.monthly_price %}{{ room_price.monthly_price|floatformat:0 }}{% elif room_price.yearly_price %}{{ room_price.yearly_price|floatformat:0 }}{% else %}—{% endif %}</span>
                  <span class="text-[13px] font-bold text-[#111111]/60">
                    {% if room_price.semester_price %}/ semester
                    {% elif room_price.monthly_price %}/ month
                    {% elif room_price.yearly_price %}/ year
                    {% endif %}
                  </span>
                </div>
              {% else %}
                <div class="text-[18px] font-extrabold text-[#111111]">Price not set</div>
              {% endif %}
              {% endwith %}
            </div>
            {% endif %}

            <div class="h-px w-full bg-black/5 my-1"></div>"""
content = content.replace(room_target, room_replacement)

with open('bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(content)
print("Updated successfully!")
