import re

with open('landing/templates/landing/property_detail.html', 'r') as f:
    content = f.read()

# We need to replace the entire <div class="scroll-animate pd-room-cards">...</div> block
# Let's use a regex to find the start and the end of the block.
# Actually, since it's quite large, it's safer to just replace from '<div class="scroll-animate pd-room-cards">'
# to the matching '</div>' which ends at line 2749-2750.
# I'll just use a simple string replacement.

old_start = '<div class="scroll-animate pd-room-cards">'
old_end = '{% empty %}'

# We'll construct the new HTML chunk
new_html = """<div class="scroll-animate pd-room-cards">
            {% for room in property.rooms.all %}
            {% if room.status == 'AVAILABLE' or room.status == 'PARTIALLY_OCCUPIED' %}
            <div class="pd-room-card">
              <div class="pd-room-card-header">
                <div>
                  <div class="pd-room-card-title">Room {{ room.room_number }} - {{ room.room_type.name }}</div>
                  <div class="pd-room-card-subtitle">{{ room.room_type.get_occupancy_type_display }}</div>
                </div>
                <div class="pd-room-card-header-right">
                  {% if room.available_slots > 2 %}
                    <span class="pd-avail-badge available">✓ {{ room.available_slots }} slots available</span>
                  {% elif room.available_slots > 0 %}
                    <span class="pd-avail-badge low">⚡ {{ room.available_slots }} person(s) left to occupy</span>
                  {% else %}
                    <span class="pd-avail-badge full">✗ Fully booked</span>
                  {% endif %}
                </div>
              </div>
              <div class="pd-room-card-body">
                <div class="pd-room-grid">
                  <div class="pd-room-details-col">
                    <!-- Room Images Carousel -->
                    {% if room.images.exists %}
                    <div style="display:flex; gap:10px; overflow-x:auto; margin-bottom:15px; padding-bottom:5px;">
                      {% for r_img in room.images.all %}
                      <img src="{{ r_img.image.url }}" alt="Room {{ room.room_number }} {{ r_img.get_image_type_display }}" style="width:120px; height:80px; object-fit:cover; border-radius:8px; flex-shrink:0;">
                      {% endfor %}
                    </div>
                    {% endif %}
                    
                    <h4>Room Features</h4>
                    <div class="pd-room-feature">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                      {{ room.room_type.get_bed_type_display }} bed{% if room.room_type.beds_per_room > 1 %}s (×{{ room.room_type.beds_per_room }}){% endif %}
                    </div>
                    {% if room.room_type.wifi_available %}
                    <div class="pd-room-feature">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                      WiFi included
                    </div>
                    {% endif %}
                    {% if room.room_type.private_bathroom %}
                    <div class="pd-room-feature">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                      Private bathroom
                    </div>
                    {% endif %}
                  </div>
                  
                  <div class="pd-room-pricing-col">
                    <h4>Pricing Options</h4>
                    {% with primary_price=room.room_type.pricing_models.first %}
                    {% if primary_price %}
                    <div class="pd-price-block">
                      <div class="pd-price-hero">
                        <div class="pd-price-top">
                          <span class="pd-price-pill">{{ primary_price.get_payment_type_display }}</span>
                          <span class="pd-price-subtle">Choose a plan that fits your stay</span>
                        </div>
                        <div class="pd-price-main">
                          GH₵ {% if primary_price.semester_price %}{{ primary_price.semester_price|floatformat:0 }}{% elif primary_price.monthly_price %}{{ primary_price.monthly_price|floatformat:0 }}{% else %}Contact{% endif %}
                        </div>
                      </div>
                    </div>
                    {% else %}
                    <div style="font-size:13px;color:var(--muted);">Contact for pricing</div>
                    {% endif %}
                    {% endwith %}
                  </div>
                </div>
              </div>
              <div class="pd-room-card-footer">
                <div class="pd-slots-info">
                  {% if room.available_slots > 0 %}
                  {{ room.available_slots }} of {{ room.total_slots }} slots open
                  {% else %}
                  All {{ room.total_slots }} slots occupied
                  {% endif %}
                </div>
                {% if room.available_slots > 0 %}
                <div class="pd-house-rules-ack" id="ack-room-{{ room.id }}">
                  <label class="pd-ack-label">
                    <input type="checkbox" class="pd-ack-check" id="check-room-{{ room.id }}"
                           onchange="toggleBookBtn('room', '{{ room.id }}')"
                           data-room-type-id="{{ room.id }}">
                    <span class="pd-ack-text">
                      I agree to the house rules.
                    </span>
                  </label>
                  <a href="{% url 'bookings:initiate_booking' property.id %}?room_id={{ room.id }}"
                     id="bookbtn-room-{{ room.id }}"
                     class="pd-book-btn pd-book-btn--disabled"
                     onclick="return handleBookClick(event, 'room', '{{ room.id }}', '{{ property.id }}')"
                     data-initiate-url="{% url 'bookings:initiate_booking' property.id %}?room_id={{ room.id }}">
                    Book This Room
                  </a>
                </div>
                {% else %}
                <a href="#rooms" class="pd-book-btn pd-book-btn--full" disabled>Fully Booked</a>
                {% endif %}
              </div>
            </div>
            {% endif %}
            {% empty %}"""

# We'll use regex to replace from old_start to old_end
pattern = re.compile(re.escape(old_start) + r'.*?' + re.escape(old_end), re.DOTALL)
new_content, count = pattern.subn(new_html, content)

if count > 0:
    with open('landing/templates/landing/property_detail.html', 'w') as f:
        f.write(new_content)
    print(f"Successfully replaced block. Count: {count}")
else:
    print("Could not find the block to replace!")
