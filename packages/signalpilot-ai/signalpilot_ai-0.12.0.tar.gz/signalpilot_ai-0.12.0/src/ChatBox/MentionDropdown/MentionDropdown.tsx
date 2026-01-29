/**
 * MentionDropdown Component
 *
 * React component for the @ mention dropdown.
 * Complete implementation matching all features of the original ChatContextMenu.
 *
 * Features:
 * - Two-level navigation (categories → items)
 * - Database schema shown at top when available
 * - Search with relevance scoring
 * - Keyboard navigation (arrows wrap around)
 * - Click and keyboard selection
 * - Loading states (initial and refreshing)
 * - Empty state messages per category
 * - Focus management (search input auto-focus)
 * - Click outside to close (via backdrop element)
 * - Scroll selected item into view
 * - Proper viewport overflow handling
 *
 * Note: This component uses pure React patterns for navigation and selection.
 * Navigable items are computed as derived state, not queried from DOM.
 */
import React, {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
  useState
} from 'react';
import {
  IMentionContext,
  MentionCategory,
  MentionDropdownProps,
  MentionDropdownRef,
  ViewType
} from './types';
import { CategoryItem } from './CategoryItem';
import { ContextItem } from './ContextItem';
import { SearchInput } from './SearchInput';
import { CategoryHeader } from './CategoryHeader';
import { LoadingIndicator } from './LoadingIndicator';
import { Separator } from './Separator';
import { MENTION_CATEGORIES } from '@/ChatBox/Context/ChatContextLoaders';
import { ContextCacheService } from '@/ChatBox/Context/ContextCacheService';
import { useContextCacheStore } from '@/stores/contextCacheStore';
import {
  calculateRelevanceScore,
  getCaretCoordinates,
  getCategoryForType,
  getEmptyMessageForCategory,
  positionDropdown
} from '@/ChatBox/Context/ChatContextMenuUtils';

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

/** Represents a navigable item in the dropdown (either a category or a context item) */
type NavigableItem =
  | { type: 'category'; categoryId: string }
  | { type: 'item'; item: IMentionContext; categoryId?: string };

// ═══════════════════════════════════════════════════════════════
// COMPONENT
// ═══════════════════════════════════════════════════════════════

export const MentionDropdown = forwardRef<
  MentionDropdownRef,
  MentionDropdownProps
>(
  (
    { inputElement, parentElement, onContextSelected, onVisibilityChange },
    ref
  ) => {
    // ═══════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════

    const [isVisible, setIsVisible] = useState(false);
    const [currentView, setCurrentView] = useState<ViewType>('categories');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(
      null
    );
    const [selectedIndex, setSelectedIndex] = useState(0);
    const [searchText, setSearchText] = useState('');
    const [currentMentionStart, setCurrentMentionStart] = useState(-1);
    const [currentMentionText, setCurrentMentionText] = useState('');
    // Start with loading=true to show loader on fresh app load until contexts are ready
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [contextItems, setContextItems] = useState<
      Map<string, IMentionContext[]>
    >(new Map());
    const [position, setPosition] = useState({ top: 0, left: 0 });

    // ═══════════════════════════════════════════════════════════════
    // REFS
    // ═══════════════════════════════════════════════════════════════

    const dropdownRef = useRef<HTMLDivElement>(null);
    const contentRef = useRef<HTMLDivElement>(null);
    const searchInputRef = useRef<HTMLInputElement>(null);
    const contextCacheService = useRef(ContextCacheService.getInstance());

    // Categories constant
    const categories: MentionCategory[] = MENTION_CATEGORIES;

    // ═══════════════════════════════════════════════════════════════
    // POSITIONING
    // ═══════════════════════════════════════════════════════════════

    const updatePosition = useCallback(() => {
      if (!inputElement || !isVisible || !dropdownRef.current) return;

      const coords = getCaretCoordinates(inputElement);

      // Use the positionDropdown utility for consistency with original
      positionDropdown(dropdownRef.current, coords);

      // Get the computed position
      const style = dropdownRef.current.style;
      setPosition({
        top: parseInt(style.top, 10) || 0,
        left: parseInt(style.left, 10) || 0
      });
    }, [inputElement, isVisible]);

    // ═══════════════════════════════════════════════════════════════
    // CONTEXT LOADING
    // ═══════════════════════════════════════════════════════════════

    const loadContexts = useCallback(async () => {
      setIsLoading(true);
      try {
        const cachedContexts = await contextCacheService.current.getContexts();
        setContextItems(cachedContexts);
      } catch (error) {
        console.warn('[MentionDropdown] Failed to load contexts:', error);
      } finally {
        setIsLoading(false);
      }
    }, []);

    const loadContextsWithRefresh = useCallback(async () => {
      const cacheStore = useContextCacheStore.getState();
      const cachedContexts = cacheStore.getCachedContexts();
      const cacheTimestamp = cacheStore.contextCacheTimestamp;

      // If cache is empty and has never been loaded (timestamp=0), show loading
      const isCacheEmpty = cachedContexts.size === 0 || cacheTimestamp === 0;

      // Check if contexts are currently being loaded in the background
      if (cacheStore.isLoading()) {
        setIsLoading(true);
        setIsRefreshing(true);

        // Wait for loading to complete
        const checkLoading = setInterval(async () => {
          if (!useContextCacheStore.getState().isLoading()) {
            clearInterval(checkLoading);
            setIsRefreshing(false);
            await loadContexts();
          }
        }, 100);
      } else if (isCacheEmpty) {
        // Cache is empty and not loading - need to load from scratch
        setIsLoading(true);
        await loadContexts();
      } else {
        // Cache has data, load it (will show existing data quickly)
        await loadContexts();
      }
    }, [loadContexts]);

    // ═══════════════════════════════════════════════════════════════
    // VISIBILITY CONTROL
    // ═══════════════════════════════════════════════════════════════

    const show = useCallback(
      (mentionStart: number) => {
        setCurrentMentionStart(mentionStart);
        setCurrentMentionText('');
        setSearchText('');
        setCurrentView('categories');
        setSelectedCategory(null);
        setSelectedIndex(0);
        setIsVisible(true);
        onVisibilityChange?.(true);
        void loadContextsWithRefresh();
      },
      [loadContextsWithRefresh, onVisibilityChange]
    );

    const hide = useCallback(() => {
      setIsVisible(false);
      setCurrentMentionStart(-1);
      setCurrentMentionText('');
      setCurrentView('categories');
      setSelectedCategory(null);
      onVisibilityChange?.(false);
    }, [onVisibilityChange]);

    // ═══════════════════════════════════════════════════════════════
    // FILTERING & DATA RETRIEVAL (moved up for use in navigableItems)
    // ═══════════════════════════════════════════════════════════════

    // Get database schema item if available
    const getDatabaseSchema = useCallback((): IMentionContext | null => {
      const dataItems = contextItems.get('data') || [];
      return dataItems.find(item => item.id === 'database-schema') || null;
    }, [contextItems]);

    // Check if database schema matches search
    const matchesDatabaseSchema = useCallback(
      (dbSchema: IMentionContext | null): boolean => {
        if (!dbSchema) return false;
        if (!searchText || searchText.length === 0) return true;
        const score = calculateRelevanceScore(dbSchema, searchText);
        return score > 500;
      },
      [searchText]
    );

    // Get filtered items for a category
    const getFilteredItems = useCallback(
      (categoryId: string): IMentionContext[] => {
        const items = contextItems.get(categoryId) || [];

        // Filter out directories for data category (show flat list of files)
        let filtered =
          categoryId === 'data'
            ? items.filter(
                item => !item.isDirectory && item.id !== 'database-schema'
              )
            : items;

        if (!searchText) {
          return filtered.sort((a, b) => a.name.localeCompare(b.name));
        }

        // Filter and score items
        const scored = filtered
          .map(item => ({
            item,
            score: calculateRelevanceScore(item, searchText)
          }))
          .filter(({ score }) => score > 500)
          .sort(
            (a, b) =>
              b.score - a.score || a.item.name.localeCompare(b.item.name)
          );

        return scored.slice(0, 15).map(({ item }) => item);
      },
      [contextItems, searchText]
    );

    // Get matching items across all categories (for category view search)
    const getMatchingItems = useCallback((): IMentionContext[] => {
      if (!searchText || searchText.length === 0) return [];

      const matching: Array<{ item: IMentionContext; score: number }> = [];

      for (const [categoryId, items] of contextItems.entries()) {
        const itemsToSearch =
          categoryId === 'data'
            ? items.filter(
                item => !item.isDirectory && item.id !== 'database-schema'
              )
            : items;

        for (const item of itemsToSearch) {
          const score = calculateRelevanceScore(item, searchText);
          if (score > 500) {
            matching.push({ item, score });
          }
        }
      }

      return matching
        .sort(
          (a, b) => b.score - a.score || a.item.name.localeCompare(b.item.name)
        )
        .slice(0, 10)
        .map(({ item }) => item);
    }, [contextItems, searchText]);

    // ═══════════════════════════════════════════════════════════════
    // COMPUTED NAVIGABLE ITEMS (replaces DOM queries)
    // ═══════════════════════════════════════════════════════════════

    /**
     * Compute flat list of navigable items based on current view and search.
     * This replaces querySelectorAll for navigation - pure React state.
     */
    const navigableItems = useMemo((): NavigableItem[] => {
      const items: NavigableItem[] = [];

      if (currentView === 'categories' && !isLoading) {
        const dbSchema = getDatabaseSchema();
        const showDbSchema = matchesDatabaseSchema(dbSchema);
        const matchingItems = getMatchingItems();
        const hasMatchingItems = matchingItems.length > 0;
        const showCategories = !hasMatchingItems || searchText.length < 2;

        // Database schema at top
        if (showDbSchema && dbSchema) {
          items.push({ type: 'item', item: dbSchema, categoryId: 'data' });
        }

        // Matching items from search
        if (hasMatchingItems) {
          for (const item of matchingItems) {
            const categoryLabel = getCategoryForType(item.type);
            items.push({ type: 'item', item, categoryId: categoryLabel });
          }
        }

        // Category list
        if (showCategories) {
          for (const category of categories) {
            items.push({ type: 'category', categoryId: category.id });
          }
        }
      } else if (currentView === 'items' && selectedCategory && !isLoading) {
        // Items view
        const filteredItems = getFilteredItems(selectedCategory);
        for (const item of filteredItems) {
          items.push({ type: 'item', item });
        }
      }

      return items;
    }, [
      currentView,
      isLoading,
      searchText,
      selectedCategory,
      categories,
      getDatabaseSchema,
      matchesDatabaseSchema,
      getMatchingItems,
      getFilteredItems
    ]);

    // ═══════════════════════════════════════════════════════════════
    // NAVIGATION
    // ═══════════════════════════════════════════════════════════════

    const navigate = useCallback(
      (direction: 'up' | 'down') => {
        const itemCount = navigableItems.length;
        if (itemCount === 0) return;

        setSelectedIndex(prev => {
          if (direction === 'down') {
            return (prev + 1) % itemCount;
          } else {
            return prev <= 0 ? itemCount - 1 : prev - 1;
          }
        });
      },
      [navigableItems.length]
    );

    // ═══════════════════════════════════════════════════════════════
    // CATEGORY SELECTION
    // ═══════════════════════════════════════════════════════════════

    const selectCategory = useCallback((categoryId: string) => {
      setSelectedCategory(categoryId);
      setCurrentView('items');
      setSelectedIndex(0);
      setSearchText('');

      // Focus search input after transition
      setTimeout(() => searchInputRef.current?.focus(), 0);
    }, []);

    const goBack = useCallback(() => {
      setCurrentView('categories');
      setSelectedCategory(null);
      setSelectedIndex(0);
    }, []);

    // ═══════════════════════════════════════════════════════════════
    // ITEM SELECTION
    // ═══════════════════════════════════════════════════════════════

    const selectItem = useCallback(
      (item: IMentionContext) => {
        if (!inputElement) return;

        // Get current input value
        const inputValue = inputElement.textContent || '';
        const beforeMention = inputValue.substring(0, currentMentionStart);
        const currentMentionEnd =
          currentMentionStart + 1 + currentMentionText.length;
        const afterMention = inputValue.substring(currentMentionEnd);

        // Format: @item_name (replace spaces with underscores)
        const displayName = item.name.replace(/\s+/g, '_');
        const replacement = `@${displayName} `;

        // Update input value
        inputElement.textContent = beforeMention + replacement + afterMention;

        // Dispatch input event to trigger any listeners
        const inputEvent = new Event('input', { bubbles: true });
        inputElement.dispatchEvent(inputEvent);

        // Set cursor position after the inserted mention
        const newCursorPosition = currentMentionStart + replacement.length;
        const selection = window.getSelection();
        if (selection && inputElement.firstChild) {
          const range = document.createRange();
          const walker = document.createTreeWalker(
            inputElement,
            NodeFilter.SHOW_TEXT
          );
          let currentOffset = 0;
          let targetNode: Node | null = null;
          let targetOffset = 0;

          while (walker.nextNode()) {
            const node = walker.currentNode;
            const nodeLength = node.textContent?.length || 0;
            if (currentOffset + nodeLength >= newCursorPosition) {
              targetNode = node;
              targetOffset = newCursorPosition - currentOffset;
              break;
            }
            currentOffset += nodeLength;
          }

          if (targetNode) {
            range.setStart(
              targetNode,
              Math.min(targetOffset, targetNode.textContent?.length || 0)
            );
            range.collapse(true);
            selection.removeAllRanges();
            selection.addRange(range);
          }
        }

        // Hide dropdown
        hide();

        // Focus input
        inputElement.focus();

        // Invoke callback
        onContextSelected?.(item);
      },
      [
        inputElement,
        currentMentionStart,
        currentMentionText,
        hide,
        onContextSelected
      ]
    );

    /**
     * Select the currently highlighted item.
     * Uses navigableItems array instead of DOM queries.
     */
    const selectHighlighted = useCallback(() => {
      if (selectedIndex < 0 || selectedIndex >= navigableItems.length) return;

      const navItem = navigableItems[selectedIndex];

      if (navItem.type === 'category') {
        // Handle category selection
        selectCategory(navItem.categoryId);
      } else {
        // Handle item selection
        selectItem(navItem.item);
      }
    }, [selectedIndex, navigableItems, selectCategory, selectItem]);

    // ═══════════════════════════════════════════════════════════════
    // UPDATE MENTION TEXT
    // ═══════════════════════════════════════════════════════════════

    const updateMentionText = useCallback((text: string) => {
      setCurrentMentionText(text);
      setSearchText(text);
      setSelectedIndex(0);
    }, []);

    // ═══════════════════════════════════════════════════════════════
    // IMPERATIVE HANDLE
    // ═══════════════════════════════════════════════════════════════

    useImperativeHandle(
      ref,
      () => ({
        show,
        hide,
        isVisible: () => isVisible,
        selectHighlighted,
        navigate,
        updateMentionText
      }),
      [show, hide, isVisible, selectHighlighted, navigate, updateMentionText]
    );

    // ═══════════════════════════════════════════════════════════════
    // EFFECTS
    // ═══════════════════════════════════════════════════════════════

    // Update position when visible
    useEffect(() => {
      if (isVisible) {
        updatePosition();
      }
    }, [isVisible, updatePosition, searchText, currentView]);

    // Scroll selected item into view using data-nav-index attribute
    const selectedItemRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
      if (!contentRef.current || selectedIndex < 0) return;

      // Find the element with matching data-nav-index
      const selectedEl = contentRef.current.querySelector(
        `[data-nav-index="${selectedIndex}"]`
      );
      if (selectedEl) {
        selectedEl.scrollIntoView({ block: 'nearest' });
      }
    }, [selectedIndex]);

    // Focus search input when dropdown becomes visible
    useEffect(() => {
      if (isVisible && searchInputRef.current) {
        setTimeout(() => searchInputRef.current?.focus(), 0);
      }
    }, [isVisible]);

    // Handle click outside via backdrop (React pattern, not document.addEventListener)
    const handleBackdropClick = useCallback(() => {
      hide();
    }, [hide]);

    // ═══════════════════════════════════════════════════════════════
    // EVENT HANDLERS
    // ═══════════════════════════════════════════════════════════════

    const handleSearchChange = useCallback((value: string) => {
      setSearchText(value);
      setSelectedIndex(0);
    }, []);

    const handleSearchKeyDown = useCallback(
      (event: React.KeyboardEvent) => {
        switch (event.key) {
          case 'ArrowDown':
            event.preventDefault();
            navigate('down');
            break;
          case 'ArrowUp':
            event.preventDefault();
            navigate('up');
            break;
          case 'Tab':
          case 'Enter':
            event.preventDefault();
            selectHighlighted();
            break;
          case 'Escape':
            event.preventDefault();
            hide();
            break;
        }
      },
      [navigate, selectHighlighted, hide]
    );

    const handleCategoryClick = useCallback(
      (categoryId: string) => {
        selectCategory(categoryId);
      },
      [selectCategory]
    );

    const handleItemClick = useCallback(
      (item: IMentionContext, categoryId?: string) => {
        if (currentView === 'categories' && categoryId) {
          setSelectedCategory(categoryId);
        }
        selectItem(item);
      },
      [currentView, selectItem]
    );

    // ═══════════════════════════════════════════════════════════════
    // RENDER HELPERS
    // ═══════════════════════════════════════════════════════════════

    const getSearchPlaceholder = useCallback((): string => {
      if (currentView === 'categories') {
        return 'Search all items...';
      }
      const categoryName =
        categories.find(c => c.id === selectedCategory)?.name || 'items';
      return `Search ${categoryName.toLowerCase()}...`;
    }, [currentView, selectedCategory, categories]);

    // Handle clicks inside dropdown - stop propagation to prevent click outside handler
    const handleDropdownClick = useCallback((event: React.MouseEvent) => {
      event.stopPropagation();
    }, []);

    // ═══════════════════════════════════════════════════════════════
    // RENDER
    // ═══════════════════════════════════════════════════════════════

    if (!isVisible) return null;

    // Compute view state for rendering
    const dbSchema = getDatabaseSchema();
    const showDbSchema =
      currentView === 'categories' && matchesDatabaseSchema(dbSchema);
    const matchingItems =
      currentView === 'categories' ? getMatchingItems() : [];
    const hasMatchingItems = matchingItems.length > 0;
    const showCategories =
      currentView === 'categories' &&
      (!hasMatchingItems || searchText.length < 2);

    // Track item indices for active state and data-nav-index
    let itemIndex = 0;

    return (
      <>
        {/* Backdrop for click-outside handling (React pattern) */}
        <div
          className="sage-ai-mention-backdrop"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            zIndex: 149999,
            background: 'transparent'
          }}
          onClick={handleBackdropClick}
        />

        <div
          ref={dropdownRef}
          className={`sage-ai-mention-dropdown${isVisible ? ' visible' : ''}`}
          style={{
            position: 'fixed',
            zIndex: 150000
          }}
          onClick={handleDropdownClick}
        >
          {/* Header */}
          <div className="sage-ai-mention-header-container">
            {currentView === 'items' && selectedCategory && (
              <CategoryHeader
                categoryName={
                  categories.find(c => c.id === selectedCategory)?.name ||
                  selectedCategory
                }
                onBack={goBack}
              />
            )}
            <SearchInput
              value={searchText}
              placeholder={getSearchPlaceholder()}
              onChange={handleSearchChange}
              onKeyDown={handleSearchKeyDown}
              autoFocus
              inputRef={searchInputRef}
            />
          </div>

          {/* Content */}
          <div ref={contentRef} className="sage-ai-mention-content">
            {/* Loading state */}
            {isLoading && <LoadingIndicator message="Loading contexts..." />}

            {/* Categories view */}
            {currentView === 'categories' && !isLoading && (
              <>
                {/* Database schema at top */}
                {showDbSchema && dbSchema && (
                  <div data-nav-index={itemIndex}>
                    <ContextItem
                      key={`db-schema-${dbSchema.id}`}
                      item={dbSchema}
                      isActive={selectedIndex === itemIndex++}
                      categoryLabel="data"
                      onClick={() => handleItemClick(dbSchema, 'data')}
                    />
                  </div>
                )}

                {/* Matching items from search */}
                {hasMatchingItems &&
                  matchingItems.map(item => {
                    const categoryLabel = getCategoryForType(item.type);
                    const currentIndex = itemIndex++;
                    return (
                      <div
                        key={`match-${item.id}`}
                        data-nav-index={currentIndex}
                      >
                        <ContextItem
                          item={item}
                          isActive={selectedIndex === currentIndex}
                          categoryLabel={categoryLabel}
                          onClick={() => handleItemClick(item, categoryLabel)}
                        />
                      </div>
                    );
                  })}

                {/* Separator before categories */}
                {(showDbSchema || hasMatchingItems) && showCategories && (
                  <Separator text="Categories" />
                )}

                {/* Category list */}
                {showCategories &&
                  categories.map(category => {
                    const currentIndex = itemIndex++;
                    return (
                      <div key={category.id} data-nav-index={currentIndex}>
                        <CategoryItem
                          category={category}
                          isActive={selectedIndex === currentIndex}
                          onClick={() => handleCategoryClick(category.id)}
                        />
                      </div>
                    );
                  })}

                {/* Refreshing indicator */}
                {isRefreshing && (
                  <LoadingIndicator message="Refreshing contexts..." />
                )}
              </>
            )}

            {/* Items view */}
            {currentView === 'items' && selectedCategory && !isLoading && (
              <>
                {getFilteredItems(selectedCategory).length === 0 ? (
                  <div className="sage-ai-mention-empty">
                    {getEmptyMessageForCategory(selectedCategory)}
                  </div>
                ) : (
                  getFilteredItems(selectedCategory).map((item, index) => (
                    <div key={item.id} data-nav-index={index}>
                      <ContextItem
                        item={item}
                        isActive={selectedIndex === index}
                        onClick={() => selectItem(item)}
                      />
                    </div>
                  ))
                )}
              </>
            )}
          </div>
        </div>
      </>
    );
  }
);

MentionDropdown.displayName = 'MentionDropdown';

export default MentionDropdown;
