/**
 * منطق انتخاب چهارسطحی در سمت کاربر
 *
 * انتخاب کاربر به‌صورت مجموعه‌های صریح در چهار سطح نگه داشته می‌شود
 * (بخش، ماژول، زیرماژول، زیرمجموعه + نقاط AI). تابع `derive` انتخاب صریح را
 * به مجموعه «فعال» گسترش می‌دهد — دقیقاً هم‌راستا با `expand_selection` در
 * بک‌اند، تا وضعیت چک‌باکس‌ها بی‌درنگ و بدون انتظار برای سرور درست باشد.
 *
 * قاعده انتخاب/لغو انتخاب:
 *   - انتخاب یک گره، همه زیرمجموعه‌هایش را فعال می‌کند (و صریح نگه نمی‌دارد).
 *   - لغو انتخاب یک گره که از والدش فعال شده، والد را به فرزندان باقی‌مانده
 *     «ماده‌سازی» (materialize) می‌کند تا بقیه انتخاب‌ها حفظ شوند.
 *   - وقتی همه فرزندان یک والد انتخاب شوند، به‌جای فهرست فرزندان، خود والد
 *     انتخاب می‌شود (فشرده‌سازی) تا payload ارسالی کوچک بماند.
 */

const LEVELS = ['sections', 'modules', 'groups', 'items']

export function emptySelection(mode = 'custom') {
  return { sections: [], modules: [], groups: [], items: [], ai_points: [], mode }
}

function asSet(values) {
  return new Set(values || [])
}

/** ساخت نگاشت‌های سلسله‌مراتب از کاتالوگ */
export function buildHierarchy(catalog) {
  const sections = catalog?.sections || []
  const sectionByCode = new Map()
  const moduleByCode = new Map()
  const groupByCode = new Map()
  const itemByCode = new Map()
  const moduleOfGroup = new Map()
  const moduleOfItem = new Map()
  const groupOfItem = new Map()
  const sectionOfModule = new Map()
  const aiItems = new Set()

  sections.forEach((section) => {
    sectionByCode.set(section.code, section)
    ;(section.modules || []).forEach((module) => {
      moduleByCode.set(module.code, module)
      sectionOfModule.set(module.code, section.code)
      ;(module.groups || []).forEach((group) => {
        groupByCode.set(group.code, group)
        moduleOfGroup.set(group.code, module.code)
        ;(group.items || []).forEach((item) => {
          itemByCode.set(item.code, item)
          moduleOfItem.set(item.code, module.code)
          groupOfItem.set(item.code, group.code)
          if (item.ai) aiItems.add(item.code)
        })
      })
    })
  })

  return {
    sections,
    sectionByCode,
    moduleByCode,
    groupByCode,
    itemByCode,
    moduleOfGroup,
    moduleOfItem,
    groupOfItem,
    sectionOfModule,
    aiItems,
  }
}

/** گسترش انتخاب صریح به مجموعه کدهای فعال */
export function derive(hierarchy, selection) {
  const explicit = {
    sections: asSet(selection.sections),
    modules: asSet(selection.modules),
    groups: asSet(selection.groups),
    items: asSet(selection.items),
    ai: asSet(selection.ai_points),
  }

  const mode = selection.mode || 'custom'
  if (mode === 'all') {
    return {
      explicit,
      sections: new Set(hierarchy.sectionByCode.keys()),
      modules: new Set(hierarchy.moduleByCode.keys()),
      groups: new Set(hierarchy.groupByCode.keys()),
      items: new Set(hierarchy.itemByCode.keys()),
      ai: new Set(hierarchy.aiItems),
      all: true,
    }
  }
  if (mode === 'none') {
    return {
      explicit,
      sections: new Set(),
      modules: new Set(),
      groups: new Set(),
      items: new Set(),
      ai: new Set(),
      none: true,
    }
  }

  const sections = new Set(explicit.sections)
  const modules = new Set(explicit.modules)
  const groups = new Set(explicit.groups)
  const items = new Set(explicit.items)
  const ai = new Set(explicit.ai)

  sections.forEach((code) => {
    const section = hierarchy.sectionByCode.get(code)
    if (!section) return
    ;(section.modules || []).forEach((module) => modules.add(module.code))
  })

  modules.forEach((code) => {
    const module = hierarchy.moduleByCode.get(code)
    if (!module) return
    const sectionCode = hierarchy.sectionOfModule.get(code)
    if (sectionCode) sections.add(sectionCode)
    ;(module.groups || []).forEach((group) => {
      groups.add(group.code)
      ;(group.items || []).forEach((item) => {
        items.add(item.code)
        if (item.ai) ai.add(item.code)
      })
    })
  })

  groups.forEach((code) => {
    const group = hierarchy.groupByCode.get(code)
    if (!group) return
    const moduleCode = hierarchy.moduleOfGroup.get(code)
    if (moduleCode) modules.add(moduleCode)
    ;(group.items || []).forEach((item) => {
      items.add(item.code)
      if (item.ai) ai.add(item.code)
    })
  })

  items.forEach((code) => {
    const moduleCode = hierarchy.moduleOfItem.get(code)
    if (moduleCode) modules.add(moduleCode)
    const groupCode = hierarchy.groupOfItem.get(code)
    if (groupCode) groups.add(groupCode)
    if (hierarchy.aiItems.has(code)) ai.add(code)
  })

  // نقاط AI فقط وقتی فعال‌اند که زیرمجموعه‌شان فعال باشد
  const aiFiltered = new Set([...ai].filter((code) => items.has(code)))

  return { sections, modules, groups, items, ai: aiFiltered, explicit }
}

function selectionFrom(sets, mode = 'custom') {
  return {
    sections: [...sets.sections].sort(),
    modules: [...sets.modules].sort(),
    groups: [...sets.groups].sort(),
    items: [...sets.items].sort(),
    ai_points: [...sets.ai].sort(),
    mode,
  }
}

function copyExplicit(derived) {
  return {
    sections: new Set(derived.explicit.sections),
    modules: new Set(derived.explicit.modules),
    groups: new Set(derived.explicit.groups),
    items: new Set(derived.explicit.items),
    ai: new Set(derived.explicit.ai),
  }
}

/** فرزندان یک گره در سطح پایین‌تر */
function childrenOf(hierarchy, level, code) {
  if (level === 'sections') {
    const section = hierarchy.sectionByCode.get(code)
    return (section?.modules || []).map((m) => m.code)
  }
  if (level === 'modules') {
    const module = hierarchy.moduleByCode.get(code)
    return (module?.groups || []).map((g) => g.code)
  }
  if (level === 'groups') {
    const group = hierarchy.groupByCode.get(code)
    return (group?.items || []).map((i) => i.code)
  }
  return []
}

function levelOfCode(hierarchy, code) {
  if (hierarchy.sectionByCode.has(code)) return 'sections'
  if (hierarchy.moduleByCode.has(code)) return 'modules'
  if (hierarchy.groupByCode.has(code)) return 'groups'
  return 'items'
}

function parentOf(hierarchy, level, code) {
  if (level === 'modules') return { level: 'sections', code: hierarchy.sectionOfModule.get(code) }
  if (level === 'groups') return { level: 'modules', code: hierarchy.moduleOfGroup.get(code) }
  if (level === 'items') return { level: 'groups', code: hierarchy.groupOfItem.get(code) }
  return null
}

/** حذف یک کد و همه زیرمجموعه‌هایش از مجموعه‌های صریح */
function dropSubtree(hierarchy, sets, level, code) {
  const queue = [{ level, code }]
  while (queue.length) {
    const node = queue.shift()
    sets[node.level].delete(node.code)
    if (node.level === 'items' && hierarchy.aiItems.has(node.code)) sets.ai.delete(node.code)
    const childLevel = LEVELS[LEVELS.indexOf(node.level) + 1]
    if (childLevel) {
      childrenOf(hierarchy, node.level, node.code).forEach((child) =>
        queue.push({ level: childLevel, code: child }),
      )
    }
  }
}

/** حذف فقط فرزندان یک گره (برای وقتی خود گره تازه انتخاب شده است) */
function dropChildren(hierarchy, sets, level, code) {
  const childLevel = LEVELS[LEVELS.indexOf(level) + 1]
  if (!childLevel) return
  childrenOf(hierarchy, level, code).forEach((child) => dropSubtree(hierarchy, sets, childLevel, child))
}

/** ماده‌سازی والد: جایگزینی انتخاب والد با فهرست صریح فرزندان (به‌جز مسیر هدف) */
function materializeAncestors(hierarchy, sets, level, code) {
  let current = { level, code }
  const chain = []
  while (current) {
    chain.unshift(current)
    current = parentOf(hierarchy, current.level, current.code)
  }

  for (let i = 0; i < chain.length - 1; i += 1) {
    const parent = chain[i]
    const child = chain[i + 1]
    if (!sets[parent.level].has(parent.code)) continue
    sets[parent.level].delete(parent.code)
    childrenOf(hierarchy, parent.level, parent.code)
      .filter((sibling) => sibling !== child.code)
      .forEach((sibling) => sets[child.level].add(sibling))
  }
}

/** فشرده‌سازی: اگر همه فرزندان یک والد فعال شدند، والد جایگزین می‌شود */
function collapse(hierarchy, sets, level, code) {
  let current = parentOf(hierarchy, level, code)
  while (current) {
    const siblings = childrenOf(hierarchy, current.level, current.code)
    const childLevel = LEVELS[LEVELS.indexOf(current.level) + 1]
    if (!siblings.length) break
    const allSelected = siblings.every((sibling) => sets[childLevel].has(sibling))
    if (!allSelected) break
    siblings.forEach((sibling) => sets[childLevel].delete(sibling))
    sets[current.level].add(current.code)
    current = parentOf(hierarchy, current.level, current.code)
  }
}

/** انتخاب یا لغو انتخاب یک گره در هر سطح */
export function toggle(hierarchy, selection, code) {
  const level = levelOfCode(hierarchy, code)
  const derived = derive(hierarchy, selection)
  const isActive = derived[level].has(code)
  const sets = copyExplicit(derived)
  const mode = selection.mode === 'all' || selection.mode === 'none' ? 'custom' : selection.mode || 'custom'

  if (isActive) {
    materializeAncestors(hierarchy, sets, level, code)
    dropSubtree(hierarchy, sets, level, code)
  } else {
    sets[level].add(code)
    dropChildren(hierarchy, sets, level, code)
    if (level === 'items' && hierarchy.aiItems.has(code)) sets.ai.add(code)
    collapse(hierarchy, sets, level, code)
  }

  return selectionFrom(sets, mode)
}

/** لغو انتخاب یک نقطه AI بدون دست‌زدن به خود زیرمجموعه */
export function toggleAiPoint(hierarchy, selection, code) {
  const derived = derive(hierarchy, selection)
  const sets = copyExplicit(derived)
  const mode = selection.mode || 'custom'

  if (!derived.items.has(code)) {
    // ابتدا خود زیرمجموعه فعال می‌شود
    sets.items.add(code)
    sets.ai.add(code)
    collapse(hierarchy, sets, 'items', code)
    return selectionFrom(sets, mode)
  }

  if (derived.explicit.ai.has(code) && !isImpliedAi(hierarchy, derived, code)) {
    sets.ai.delete(code)
    return selectionFrom(sets, mode)
  }

  // نقطه از والدش فعال شده → والد ماده‌سازی و نقطه حذف می‌شود
  materializeAncestors(hierarchy, sets, 'items', code)
  sets.ai.delete(code)
  return selectionFrom(sets, mode)
}

function isImpliedAi(hierarchy, derived, code) {
  const groupCode = hierarchy.groupOfItem.get(code)
  const moduleCode = hierarchy.moduleOfItem.get(code)
  const sectionCode = moduleCode ? hierarchy.sectionOfModule.get(moduleCode) : null
  return derived.explicit.groups.has(groupCode) || derived.explicit.modules.has(moduleCode) || derived.explicit.sections.has(sectionCode)
}

/** انتخاب کل کاتالوگ یا پاک‌سازی کامل */
export function selectAll(mode) {
  return emptySelection(mode)
}

/** ساخت انتخاب از فهرست صریح ماژول‌ها (پریست، دستیار یا یک پروژه ذخیره‌شده) */
export function selectionFromModules(hierarchy, modules, aiPoints = null, extra = null) {
  const sets = {
    sections: new Set([...(extra?.sections || [])].filter((code) => hierarchy.sectionByCode.has(code))),
    modules: new Set([...(modules || [])].filter((code) => hierarchy.moduleByCode.has(code))),
    groups: new Set([...(extra?.groups || [])].filter((code) => hierarchy.groupByCode.has(code))),
    items: new Set([...(extra?.items || [])].filter((code) => hierarchy.itemByCode.has(code))),
    ai: new Set(),
  }
  sets.sections.forEach((code) => dropChildren(hierarchy, sets, 'sections', code))
  sets.modules.forEach((code) => {
    dropChildren(hierarchy, sets, 'modules', code)
    collapse(hierarchy, sets, 'modules', code)
  })
  sets.groups.forEach((code) => {
    dropChildren(hierarchy, sets, 'groups', code)
    collapse(hierarchy, sets, 'groups', code)
  })
  sets.items.forEach((code) => collapse(hierarchy, sets, 'items', code))
  if (aiPoints) {
    sets.ai = new Set([...aiPoints].filter((code) => hierarchy.aiItems.has(code)))
  } else {
    const derived = derive(hierarchy, selectionFrom(sets))
    sets.ai = derived.ai
  }
  return selectionFrom(sets)
}

/** شمارش سریع برای نمایش روی هر گره */
export function nodeCounts(hierarchy, derived, level, code) {
  if (level === 'sections') {
    const section = hierarchy.sectionByCode.get(code)
    const modules = (section?.modules || []).map((m) => m.code)
    const selected = modules.filter((m) => derived.modules.has(m)).length
    return { total: modules.length, selected }
  }
  if (level === 'modules') {
    const module = hierarchy.moduleByCode.get(code)
    const items = (module?.groups || []).flatMap((g) => g.items || [])
    const selected = items.filter((i) => derived.items.has(i.code)).length
    const ai = items.filter((i) => i.ai && derived.ai.has(i.code)).length
    return { total: items.length, selected, ai, aiTotal: items.filter((i) => i.ai).length }
  }
  if (level === 'groups') {
    const group = hierarchy.groupByCode.get(code)
    const items = group?.items || []
    const selected = items.filter((i) => derived.items.has(i.code)).length
    return { total: items.length, selected, aiTotal: items.filter((i) => i.ai).length }
  }
  return { total: 1, selected: derived.items.has(code) ? 1 : 0 }
}

export function checkboxState(counts) {
  if (!counts.total) return 'none'
  if (counts.selected === counts.total) return 'all'
  if (counts.selected > 0) return 'partial'
  return 'none'
}

export default {
  emptySelection,
  buildHierarchy,
  derive,
  toggle,
  toggleAiPoint,
  selectionFromModules,
  nodeCounts,
  checkboxState,
}
