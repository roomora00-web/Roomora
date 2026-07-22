import re

with open('landing/templates/landing/property_detail.html', 'r') as f:
    content = f.read()

# I want to replace everything from `<!-- Page canvas -->` to just before `<!-- Visit Modal -->` or `<div class="pd-modal-overlay" id="visit-modal"`
start_marker = '<div class="pd-canvas">'
end_marker = '<div class="pd-modal-overlay" id="visit-modal"'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1 or end_idx == -1:
    print("Markers not found!")
    exit(1)

new_body = """
<!-- Page canvas -->
<div class="pd-canvas" style="padding-top:20px; max-width:1400px; margin: 0 auto;">
  
  <!-- Breadcrumb & Share row -->
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:24px;">
    <div class="pd-breadcrumb" style="font-size:13px; color:var(--muted);">
       <a href="/" style="color:var(--muted); text-decoration:none;">All clusters</a> <span style="margin:0 8px;">/</span> <span style="color:#111111; font-weight:600;">{{ property.title }}</span> <span style="margin:0 8px;">/</span> <span style="padding:4px 10px; background:var(--canvas); border:1px solid var(--border-light); border-radius:12px; font-weight:600; color:#111111;">{{ property.get_property_type_display }}</span>
    </div>
    <div style="display:flex; gap:12px;">
       <button style="padding:8px 16px; background:var(--canvas); border:1px solid var(--border); border-radius:8px; font-size:13px; font-weight:600; color:#111111; cursor:pointer; display:flex; align-items:center; gap:8px;">
         <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"></path><polyline points="16 6 12 2 8 6"></polyline><line x1="12" y1="2" x2="12" y2="15"></line></svg>
         Share
       </button>
    </div>
  </div>
  
  <!-- Hero Image Section -->
  <div style="position:relative; width:100%; height:700px; border-radius:2px; overflow:hidden; margin-bottom:40px; background:#e2e8f0;">
    {% with main_img=property.images.first %}
    <img src="{% if main_img %}{{ main_img.image_url }}{% endif %}" style="width:100%; height:100%; object-fit:cover;" alt="{{ property.title }}" />
    {% endwith %}
    <!-- Overlay gradient -->
    <div style="position:absolute; bottom:0; left:0; width:100%; height:200px; background:linear-gradient(to top, rgba(0,0,0,0.7), transparent);"></div>
    <!-- Thumbnail Strip -->
    <div style="position:absolute; bottom:24px; left:50%; transform:translateX(-50%); display:flex; gap:8px;">
       {% for img in property.all_gallery_images|slice:":6" %}
       <div style="width:90px; height:60px; border:2px solid {% if forloop.first %}#FFFFFF{% else %}transparent{% endif %}; cursor:pointer; background:#111111;" onclick="openLightbox({{ forloop.counter0 }})">
          <img src="{{ img.image_url }}" style="width:100%; height:100%; object-fit:cover; opacity:{% if forloop.first %}1{% else %}0.6{% endif %}; transition:opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="if('{% if forloop.first %}yes{% endif %}' !== 'yes') this.style.opacity='0.6'" />
       </div>
       {% endfor %}
    </div>
  </div>
  
  <!-- Main Two Column Layout -->
  <div style="display:grid; grid-template-columns: 1fr 380px; gap:48px;">
     
     <!-- LEFT COLUMN -->
     <div>
       <!-- Title Block -->
       <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:32px;">
         <div>
           <h1 style="font-size:28px; font-weight:800; color:#111111; margin-bottom:8px; line-height:1.2;">{{ property.title }}</h1>
           <p style="color:var(--muted); font-size:15px; margin:0;">{{ property.address }}, {{ property.city }}</p>
         </div>
         <div style="padding:10px 16px; background:var(--canvas); border:1px solid var(--border); font-size:13px; font-weight:600; color:#111111; display:flex; align-items:center; gap:8px;">
           {{ property.rooms.count }} unit{{ property.rooms.count|pluralize }} available &rarr;
         </div>
       </div>
       
       <!-- Stats Grid -->
       <div style="display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--border); margin-bottom:48px;">
          <div style="padding:24px; border-bottom:1px solid var(--border); border-right:1px solid var(--border); display:flex; align-items:flex-start; gap:16px;">
             <div style="color:var(--muted); margin-top:2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path></svg></div>
             <div>
                <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">Property Style</div>
                <div style="font-weight:700; font-size:15px; color:#111111;">{{ property.get_property_type_display }}</div>
             </div>
          </div>
          <div style="padding:24px; border-bottom:1px solid var(--border); display:flex; align-items:flex-start; gap:16px;">
             <div style="color:var(--muted); margin-top:2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>
             <div>
                <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">Verification Status</div>
                <div style="font-weight:700; font-size:15px; color:#111111;">{% if property.is_verified %}Verified{% else %}Unverified{% endif %}</div>
             </div>
          </div>
          <div style="padding:24px; border-right:1px solid var(--border); display:flex; align-items:flex-start; gap:16px;">
             <div style="color:var(--muted); margin-top:2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg></div>
             <div>
                <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">Total Capacity</div>
                <div style="font-weight:700; font-size:15px; color:#111111;">{{ property.capacity|default:"50" }} Students</div>
             </div>
          </div>
          <div style="padding:24px; display:flex; align-items:flex-start; gap:16px;">
             <div style="color:var(--muted); margin-top:2px;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div>
             <div>
                <div style="font-size:12px; color:var(--muted); margin-bottom:6px;">Safety Score</div>
                <div style="font-weight:700; font-size:15px; color:#111111;">{{ property.safety_score|default:"9.0" }}/10</div>
             </div>
          </div>
       </div>
       
       <!-- About properties -->
       <div style="margin-bottom:48px;">
         <h3 style="font-size:18px; font-weight:800; margin-bottom:20px; color:#111111; line-height:1;">About properties</h3>
         <div style="font-size:14px; color:#555555; line-height:1.8; white-space:pre-wrap; margin-bottom:12px;">{{ property.description }}</div>
         <a href="#" style="font-size:13px; font-weight:700; color:#111111; text-decoration:underline;">Read more</a>
       </div>
       
       <!-- Locations -->
       <div style="margin-bottom:48px;">
         <h3 style="font-size:18px; font-weight:800; margin-bottom:20px; color:#111111; line-height:1;">Locations</h3>
         <div style="display:grid; grid-template-columns:1.2fr 0.8fr; border:1px solid var(--border);">
           <div id="property-map" style="width:100%; height:450px; background:var(--canvas);"></div>
           <div style="padding:28px;">
             <h4 style="font-size:14px; font-weight:700; margin:0 0 24px 0; color:#111111;">This residence is near with :</h4>
             {% for dest in property.proximity_destinations.all %}
             <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:24px; padding-bottom:16px; border-bottom:1px solid var(--border-light);">
               <div>
                 <div style="font-weight:700; font-size:13px; color:#111111;">{{ dest.destination_name }}</div>
                 <div style="font-size:12px; color:var(--muted); margin-top:6px;">{{ dest.distance_km }} km &bull; {{ dest.estimated_time_minutes }} min {{ dest.get_travel_mode_display|lower }}</div>
               </div>
               <div style="color:var(--muted); border:1px solid var(--border); padding:6px; display:flex; align-items:center; justify-content:center;">
                 <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>
               </div>
             </div>
             {% empty %}
             <p style="font-size:13px; color:var(--muted);">No nearby locations defined.</p>
             {% endfor %}
           </div>
         </div>
       </div>
       
       <!-- Full Specifications -->
       <div style="margin-bottom:48px;">
         <h3 style="font-size:18px; font-weight:800; margin-bottom:20px; color:#111111; line-height:1;">Full specifications</h3>
         <div style="border:1px solid var(--border);">
           
           <div style="border-bottom:1px solid var(--border);">
             <div style="padding:20px 24px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none';">
               <div style="font-weight:700; font-size:14px; color:#111111;">Amenities & Features</div>
               <div style="background:var(--canvas); padding:6px; border:1px solid var(--border-light);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg></div>
             </div>
             <div style="padding:0 24px 24px 24px; display:block;">
               <div style="display:grid; grid-template-columns:1fr 1fr; gap:16px;">
                 {% for am in property.amenities.all %}
                 <div style="font-size:13px; color:#555555; display:flex; align-items:center; gap:12px;">
                   <span style="display:block; width:3px; height:3px; background:#111111; border-radius:50%; flex-shrink:0;"></span>
                   <span style="flex:1;">{{ am.name }}</span>
                 </div>
                 {% endfor %}
               </div>
             </div>
           </div>
           
           <div style="border-bottom:1px solid var(--border);">
             <div style="padding:20px 24px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none';">
               <div style="font-weight:700; font-size:14px; color:#111111;">Utilities & Green Energy</div>
               <div style="background:var(--canvas); padding:6px; border:1px solid var(--border-light);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg></div>
             </div>
             <div style="padding:0 24px 24px 24px; display:none;">
                <div style="display:flex; flex-direction:column; gap:12px;">
                  <div style="font-size:13px; color:#555555; display:flex; gap:12px;"><span style="display:block; width:3px; height:3px; background:#111111; border-radius:50%; margin-top:7px;"></span><span><strong>Water:</strong> {{ property.water_availability }}</span></div>
                  <div style="font-size:13px; color:#555555; display:flex; gap:12px;"><span style="display:block; width:3px; height:3px; background:#111111; border-radius:50%; margin-top:7px;"></span><span><strong>Electricity:</strong> {{ property.electricity_stability }}</span></div>
                  <div style="font-size:13px; color:#555555; display:flex; gap:12px;"><span style="display:block; width:3px; height:3px; background:#111111; border-radius:50%; margin-top:7px;"></span><span><strong>Internet:</strong> {{ property.internet_availability }}</span></div>
                </div>
             </div>
           </div>
           
           <div>
             <div style="padding:20px 24px; display:flex; justify-content:space-between; align-items:center; cursor:pointer;" onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none';">
               <div style="font-weight:700; font-size:14px; color:#111111;">Community & House Rules</div>
               <div style="background:var(--canvas); padding:6px; border:1px solid var(--border-light);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg></div>
             </div>
             <div style="padding:0 24px 24px 24px; display:none;">
                <div style="font-size:13px; color:#555555; line-height:1.7; white-space:pre-wrap;">{{ property.house_rules|default:"No specific house rules provided." }}</div>
             </div>
           </div>
           
         </div>
       </div>
       
       <!-- Floor plan -->
       <div style="margin-bottom:80px;">
         <h3 style="font-size:18px; font-weight:800; margin-bottom:20px; color:#111111; line-height:1;">Floor plan</h3>
         <div style="display:grid; grid-template-columns:1fr 1fr; border:1px solid var(--border);">
           <!-- Left side image placeholder -->
           <div style="background:var(--canvas); border-right:1px solid var(--border); display:flex; align-items:center; justify-content:center; min-height:350px; color:var(--muted); padding:32px;">
              <div style="text-align:center;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><line x1="3" y1="9" x2="21" y2="9"></line><line x1="9" y1="21" x2="9" y2="9"></line></svg>
                <div style="margin-top:16px; font-size:13px; font-weight:600;">Floor plan visualization unavailable</div>
              </div>
           </div>
           <!-- Right side list -->
           <div style="padding:32px;">
             {% for room in property.rooms.all|slice:":5" %}
             <div style="display:flex; align-items:flex-start; gap:20px; margin-bottom:24px; padding-bottom:24px; border-bottom:1px dashed var(--border-light);">
               <div style="width:28px; height:28px; border-radius:50%; background:var(--canvas); display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:800; color:#111111; flex-shrink:0; border:1px solid var(--border);">{{ forloop.counter }}</div>
               <div>
                 <div style="font-weight:700; font-size:14px; color:#111111; margin-bottom:4px;">Room {{ room.room_number }}</div>
                 <div style="font-size:13px; color:var(--muted); line-height:1.5;">{{ room.room_type.room_type_name }}. {{ room.room_type.get_occupancy_type_display }}.</div>
               </div>
             </div>
             {% empty %}
             <div style="font-size:13px; color:var(--muted);">No specific rooms listed.</div>
             {% endfor %}
           </div>
         </div>
       </div>
       
     </div>
     
     <!-- RIGHT COLUMN -->
     <div>
       <div style="position:sticky; top:32px;">
       
         <!-- Price & Payment -->
         <div style="margin-bottom:32px;">
           <h3 style="font-size:16px; font-weight:700; color:#111111; margin-bottom:16px;">Price & payment</h3>
           <div style="border:1px solid var(--border); padding:32px;">
             
             <div style="margin-bottom:28px;">
               <div style="font-size:12px; color:var(--muted); margin-bottom:8px;">Total Price</div>
               {% with room_price=property.rooms.first.room_type.pricing_models.first %}
               <div style="font-size:36px; font-weight:800; color:#111111; letter-spacing:-1px;">
                 {% if room_price %}
                    GH&#8373; {% if room_price.semester_price %}{{ room_price.semester_price|floatformat:0 }}{% elif room_price.monthly_price %}{{ room_price.monthly_price|floatformat:0 }}{% else %}—{% endif %}
                 {% else %}
                    Contact for price
                 {% endif %}
               </div>
               {% endwith %}
             </div>
             
             <div style="display:flex; flex-direction:column; gap:16px; margin-bottom:32px; font-size:13px;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="color:var(--muted);">Security Deposit</span>
                  <span style="font-weight:600; color:#111111; text-align:right;">Req. on Confirmation</span>
                </div>
                <div style="border-bottom:1px dotted var(--border);"></div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="color:var(--muted);">Payment Methods</span>
                  <span style="font-weight:600; color:#111111; text-align:right;">Bank Transfer, MOMO</span>
                </div>
                <div style="border-bottom:1px dotted var(--border);"></div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="color:var(--muted);">Additional Fees</span>
                  <span style="font-weight:600; color:#111111; text-align:right;">Agency Fee (if app.)</span>
                </div>
                <div style="border-bottom:1px dotted var(--border);"></div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                  <span style="color:var(--muted);">Special Offers</span>
                  <span style="font-weight:600; color:#111111; text-align:right;">Free WiFi</span>
                </div>
             </div>
             
             <button onclick="document.getElementById('roomSelectModalOverlay').style.display='flex'" style="width:100%; padding:16px; background:#111111; color:#FFFFFF; font-weight:700; border:none; display:flex; align-items:center; justify-content:center; gap:8px; margin-bottom:12px; cursor:pointer; font-size:14px; transition:opacity 0.2s;" onmouseover="this.style.opacity='0.9'" onmouseout="this.style.opacity='1'">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                Schedule a tour / Book
             </button>
             
             <button onclick="openVisitModal()" style="width:100%; padding:16px; background:var(--canvas); color:#111111; border:1px solid var(--border); font-weight:700; display:flex; align-items:center; justify-content:center; gap:8px; cursor:pointer; font-size:14px; transition:background 0.2s;" onmouseover="this.style.background='#FFFFFF'" onmouseout="this.style.background='var(--canvas)'">
                View more detail
             </button>
           </div>
         </div>
         
         <!-- 3D Preview Placeholder -->
         <div>
           <h3 style="font-size:16px; font-weight:700; color:#111111; margin-bottom:16px;">3D Preview</h3>
           <div style="position:relative; width:100%; height:260px; background:#e2e8f0; display:flex; align-items:center; justify-content:center; cursor:pointer; overflow:hidden;">
             {% with main_img=property.images.first %}
             <img src="{% if main_img %}{{ main_img.image_url }}{% endif %}" style="width:100%; height:100%; object-fit:cover; opacity:0.5; filter:blur(3px); transform:scale(1.1);" />
             {% endwith %}
             <div style="position:absolute; width:64px; height:64px; background:rgba(17,17,17,0.7); backdrop-filter:blur(4px); border-radius:50%; display:flex; align-items:center; justify-content:center; color:#FFFFFF; z-index:2; transition:transform 0.2s;" onmouseover="this.style.transform='scale(1.1)'" onmouseout="this.style.transform='scale(1)'">
               <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
             </div>
           </div>
         </div>
         
       </div>
     </div>
     
  </div>
</div>
<!-- /Page canvas -->
\n\n"""

# Perform the replacement
final_content = content[:start_idx] + new_body + content[end_idx:]

with open('landing/templates/landing/property_detail.html', 'w') as f:
    f.write(final_content)

print("Layout replaced successfully!")
