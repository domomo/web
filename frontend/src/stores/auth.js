import { ref } from 'vue';

export const currentUser = ref(null);
export const authRevision = ref(0);

export function setCurrentUser(user) {
  authRevision.value += 1;
  currentUser.value = user || null;
}
