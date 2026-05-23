<template>
  <div class="tags-manager">
    <div class="page-header">
      <h1>{{ t('tags.title') }}</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>{{ t('common.action.create') }}
      </el-button>
    </div>

    <el-tree
      :data="tagTree"
      :props="{ label: 'name', children: 'children' }"
      node-key="id"
      default-expand-all
    >
      <template #default="{ node, data }">
        <span class="tree-node">
          <el-tag :color="data.color" size="small">{{ data.name }}</el-tag>
          <span class="node-actions">
            <el-button text size="small" @click="editTag(data)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button text size="small" type="danger" @click="deleteTag(data.id)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </span>
        </span>
      </template>
    </el-tree>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="500px">
      <el-form label-position="top">
        <el-form-item :label="t('tags.form.name')">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item :label="t('tags.form.color')">
          <el-color-picker v-model="form.color" />
        </el-form-item>
        <el-form-item :label="t('tags.form.description')">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
        <el-form-item :label="t('tags.form.parent')">
          <el-select v-model="form.parent_id" clearable>
            <el-option v-for="tag in flatTags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ t('common.btn.cancel') }}</el-button>
        <el-button type="primary" @click="handleSave">{{ t('common.btn.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>import { ref, reactive, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, Edit, Delete } from '@element-plus/icons-vue';
import { getTagTree, createTag, updateTag, deleteTag } from '@/api/tags';
const { t } = useI18n();
const tagTree = ref([]);
const dialogVisible = ref(false);
const dialogTitle = ref('');
const editingId = ref(null);
const form = reactive({
 name: '',
 color: '#3B82F6',
 description: '',
 parent_id: null,
});
const flatTags = computed(() => {
 const flatten = (nodes) => {
 const result = [];
 for (const node of nodes) {
 result.push({ id: node.id, name: node.name });
 if (node.children) {
 result.push(...flatten(node.children));
 }
 }
 return result;
 };
 return flatten(tagTree.value);
});
onMounted(async () => {
 await loadTags();
});
async function loadTags() {
 try {
 tagTree.value = await getTagTree();
 }
 catch (e) {
 ElMessage.error(t('tags.loadFailed'));
 }
}
function showCreateDialog() {
 dialogTitle.value = t('tags.create');
 editingId.value = null;
 form.name = '';
 form.color = '#3B82F6';
 form.description = '';
 form.parent_id = null;
 dialogVisible.value = true;
}
function editTag(data) {
 dialogTitle.value = t('tags.edit');
 editingId.value = data.id;
 form.name = data.name;
 form.color = data.color;
 form.description = data.description || '';
 form.parent_id = data.parent_id;
 dialogVisible.value = true;
}
async function handleSave() {
 try {
 if (editingId.value) {
 await updateTag(editingId.value, form);
 ElMessage.success(t('common.msg.saveSuccess'));
 }
 else {
 await createTag(form);
 ElMessage.success(t('common.msg.createSuccess'));
 }
 dialogVisible.value = false;
 await loadTags();
 }
 catch (e) {
 ElMessage.error(t('common.msg.saveFailed'));
 }
}
async function deleteTag(id) {
 try {
 await ElMessageBox.confirm(t('tags.delete.confirm'), t('common.msg.confirmDelete'), { type: 'warning' });
 await deleteTag(id);
 ElMessage.success(t('common.msg.deleteSuccess'));
 await loadTags();
 }
 catch (e) {
 if (e !== 'cancel') {
 ElMessage.error(t('common.msg.deleteFailed'));
 }
 }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.page-header h1 { font-size: var(--font-size-2xl); }
.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}
.node-actions {
  margin-left: auto;
  display: flex;
  gap: 4px;
}
</style>
