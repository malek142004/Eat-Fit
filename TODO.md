# TODO: Advanced Search and Review System for Nutritionists

## Phase 1: Database Models
- [x] Add missing imports (MaxValueValidator, Avg) to models.py
- [x] Add average_rating() and total_reviews() methods to Nutritionist model
- [ ] Create NutritionistReview model with rating and comment fields
- [ ] Run migrations to create new database tables

## Phase 2: Advanced Search Features
- [ ] Update nutritionist_list view to support advanced filtering:
  - Filter by speciality
  - Filter by city
  - Filter by experience range
  - Filter by rating range
  - Proximity search (geographic)
- [ ] Add sorting options (by rating, experience, fee, etc.)
- [ ] Update template with advanced search form

## Phase 3: Review and Rating System
- [ ] Create forms for adding/editing reviews
- [ ] Create views for review management (add, edit, delete)
- [ ] Update nutritionist detail view to show reviews
- [ ] Add review display to nutritionist list template
- [ ] Add star rating display components

## Phase 4: Frontend Enhancements
- [ ] Update nutritionist_list.html template with:
  - Advanced search filters
  - Rating display (stars)
  - Review count display
  - Improved sorting options
- [ ] Add JavaScript for dynamic filtering
- [ ] Style the rating components

## Phase 5: Testing and Validation
- [ ] Test all search filters work correctly
- [ ] Test review submission and display
- [ ] Validate rating calculations
- [ ] Test responsive design
