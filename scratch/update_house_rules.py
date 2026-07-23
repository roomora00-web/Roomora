import re

with open('bookings/templates/bookings/house_rules_acknowledgment.html', 'r') as f:
    content = f.read()

# 1. Update Left Column - Add Utilities & Connectivity Bento
utilities_bento = """
          <!-- Utilities Bento -->
          <div class="bg-white/80 backdrop-blur-xl border border-black/5 rounded-[32px] p-8 shadow-[0_8px_30px_rgba(0,0,0,0.04)] hover:shadow-[0_20px_40px_rgba(0,0,0,0.08)] transition-all duration-300 flex flex-col justify-between group">
            <div>
              <div class="w-12 h-12 rounded-[16px] bg-[#3B82F6]/10 flex items-center justify-center text-[#3B82F6] mb-6 transition-transform duration-300 group-hover:scale-110">
                <svg width="24" height="24" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
              </div>
              <h3 class="text-xl font-extrabold text-[#111111] mb-2">Utilities</h3>
              <ul class="space-y-3 mt-4">
                {% if property.water_availability %}
                <li class="flex items-center gap-3 text-[14px] font-medium text-[#111111]/80"><svg class="text-[#3B82F6] shrink-0" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> {{ property.water_availability }}</li>
                {% endif %}
                {% if property.electricity_stability %}
                <li class="flex items-center gap-3 text-[14px] font-medium text-[#111111]/80"><svg class="text-[#3B82F6] shrink-0" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> {{ property.electricity_stability }}</li>
                {% endif %}
                {% if property.internet_availability %}
                <li class="flex items-center gap-3 text-[14px] font-medium text-[#111111]/80"><svg class="text-[#3B82F6] shrink-0" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> {{ property.internet_availability }}</li>
                {% endif %}
              </ul>
            </div>
          </div>
"""

# We'll inject this Utilities bento by changing grid-cols-2 to grid-cols-3 (or make it a separate block).
# Let's just make the Location/Safety/Utilities grid responsive: grid-cols-1 md:grid-cols-3
content = content.replace(
    '<section class="grid grid-cols-1 md:grid-cols-2 gap-6 animate-fade-up" style="animation-delay: 0.3s;">',
    '<section class="grid grid-cols-1 md:grid-cols-3 gap-6 animate-fade-up" style="animation-delay: 0.3s;">'
)
# Insert before "<!-- Safety Bento -->"
content = content.replace(
    '          <!-- Safety Bento -->',
    utilities_bento + '          <!-- Safety Bento -->'
)

# Remove the old utility amenities from the Amenities section if they were hardcoded...
# Looking at the original:
# {% if property.water_availability %} ... Constant Water ...
old_water = """              {% if property.water_availability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#3B82F6]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Constant Water</div>
                </div>
              {% endif %}"""
old_elec = """              {% if property.electricity_stability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#EAB308]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Stable Electricity</div>
                </div>
              {% endif %}"""
old_net = """              {% if property.internet_availability %}
                <div class="flex items-center gap-4 bg-[#F9FAFB] p-4 rounded-[20px] border border-black/5">
                  <div class="bg-white p-2.5 rounded-[12px] shadow-sm"><svg class="text-[#8B5CF6]" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path d="M5 12.55a11 11 0 0 1 14.08 0 M1.42 9a16 16 0 0 1 21.16 0 M8.53 16.11a6 6 0 0 1 6.95 0 M12 20h.01"/></svg></div>
                  <div class="text-[15px] font-bold text-[#111111]">Fast Internet</div>
                </div>
              {% endif %}"""
content = content.replace(old_water, "")
content = content.replace(old_elec, "")
content = content.replace(old_net, "")

# 2. Update Right Column - Room Features
room_features = """
              <!-- Room Specific Amenities (if any) -->
              {% if room.room_type %}
              <div class="mt-4 pt-4 border-t border-black/5">
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-3">Room Features</div>
                <div class="grid grid-cols-2 gap-y-3 gap-x-4">
                  {% if room.room_type.private_bathroom %}
                  <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                    <svg class="text-[#059669]" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Private Bath
                  </div>
                  {% endif %}
                  {% if room.room_type.air_conditioning %}
                  <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                    <svg class="text-[#059669]" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Air Conditioned
                  </div>
                  {% endif %}
                  {% if room.room_type.study_desk_available %}
                  <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                    <svg class="text-[#059669]" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Study Desk
                  </div>
                  {% endif %}
                  {% if room.room_type.wardrobe_available %}
                  <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                    <svg class="text-[#059669]" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Wardrobe
                  </div>
                  {% endif %}
                  {% if room.room_type.balcony %}
                  <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                    <svg class="text-[#059669]" width="14" height="14" fill="none" stroke="currentColor" stroke-width="3" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg> Balcony
                  </div>
                  {% endif %}
                </div>
              </div>
              {% endif %}
"""
old_room_amenities = """              <!-- Room Specific Amenities (if any) -->
              {% if room.amenities.exists %}
              <div class="mt-4 pt-4 border-t border-black/5">
                <div class="text-[12px] font-extrabold uppercase tracking-wide text-[#111111]/40 mb-3">Room Amenities</div>
                <div class="grid grid-cols-2 gap-y-2 gap-x-4">
                  {% for amenity in room.amenities.all|slice:":6" %}
                    <div class="flex items-center gap-2 text-[13px] font-semibold text-[#111111]/80">
                      <svg class="text-[#111111]/40" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
                      {{ amenity.name }}
                    </div>
                  {% endfor %}
                </div>
              </div>
              {% endif %}"""
content = content.replace(old_room_amenities, room_features)

# Enhance Pricing Block
pricing_block_enhanced = """            <!-- Sleek Pricing Invoice Block -->
            <div class="bg-[#F9FAFB] rounded-[24px] p-6 border border-black/5 relative overflow-hidden shadow-inner">
              <div class="text-[12px] font-extrabold uppercase tracking-widest text-[#111111]/40 mb-3 relative z-10">Summary Price Breakdown</div>
              {% with room_price=room.room_type.pricing_models.first %}
              {% if room_price %}
                <div class="flex justify-between items-baseline mb-3">
                  <span class="text-[14px] font-bold text-[#111111]/70">Rent Rate</span>
                  <div class="text-right">
                    <span class="text-[20px] font-extrabold text-[#111111]">GH&#8373;{% if room_price.semester_price %}{{ room_price.semester_price|floatformat:0 }}{% elif room_price.monthly_price %}{{ room_price.monthly_price|floatformat:0 }}{% elif room_price.yearly_price %}{{ room_price.yearly_price|floatformat:0 }}{% else %}—{% endif %}</span>
                    <span class="text-[12px] font-bold text-[#111111]/50 block">{% if room_price.semester_price %}/ semester{% elif room_price.monthly_price %}/ month{% elif room_price.yearly_price %}/ year{% endif %}</span>
                  </div>
                </div>
                
                {% if room_price.security_deposit %}
                <div class="flex justify-between items-center py-2 border-t border-black/5">
                  <span class="text-[14px] font-bold text-[#111111]/70">Security Deposit</span>
                  <span class="text-[14px] font-extrabold text-[#111111]">GH&#8373;{{ room_price.security_deposit|floatformat:0 }}</span>
                </div>
                {% endif %}
                
                {% if room_price.maintenance_fee %}
                <div class="flex justify-between items-center py-2 border-t border-black/5">
                  <span class="text-[14px] font-bold text-[#111111]/70">Maintenance Fee</span>
                  <span class="text-[14px] font-extrabold text-[#111111]">GH&#8373;{{ room_price.maintenance_fee|floatformat:0 }}</span>
                </div>
                {% endif %}
              {% else %}
                <div class="text-[20px] font-extrabold text-[#111111] relative z-10">Price not set</div>
              {% endif %}
              {% endwith %}
            </div>"""

old_pricing = """            <!-- Sleek Pricing Invoice Block -->
            <div class="bg-[#F9FAFB] rounded-[24px] p-6 border border-black/5 relative overflow-hidden shadow-inner">
              <div class="text-[12px] font-extrabold uppercase tracking-widest text-[#111111]/40 mb-2 relative z-10">Summary Price</div>
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
            </div>"""
content = content.replace(old_pricing, pricing_block_enhanced)

with open('bookings/templates/bookings/house_rules_acknowledgment.html', 'w') as f:
    f.write(content)
print("Updated successfully")
