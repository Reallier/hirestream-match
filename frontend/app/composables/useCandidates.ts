/**
 * 候选人管理 Composable
 * 
 * 所有候选人 API 调用后端 FastAPI 服务
 */

interface Candidate {
    id: number;
    name: string;
    email?: string;
    phone?: string;
    location?: string;
    currentTitle?: string;
    currentCompany?: string;
    yearsExperience?: number;
    skills?: string[];
    status?: string;
    createdAt?: string;
}

interface CandidateListResponse {
    candidates: Candidate[];
    total: number;
}

export const useCandidates = () => {
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase;
    const { user } = useAuth();

    /**
     * 获取候选人列表
     */
    const getCandidates = async (params?: { skip?: number; limit?: number; status?: string }): Promise<CandidateListResponse> => {
        if (!user.value) {
            return { candidates: [], total: 0 };
        }

        const queryParams = new URLSearchParams();
        queryParams.append('user_id', String(user.value.id));
        if (params?.skip) queryParams.append('skip', String(params.skip));
        if (params?.limit) queryParams.append('limit', String(params.limit));
        if (params?.status) queryParams.append('status', params.status);

        const response = await $fetch<any>(`${apiBase}/api/candidates?${queryParams.toString()}`, {
            credentials: 'include'
        });

        return {
            candidates: response.candidates || [],
            total: response.total || 0
        };
    };

    /**
     * 获取候选人数量
     */
    const getCandidateCount = async (): Promise<number> => {
        if (!user.value) return 0;

        const response = await $fetch<any>(`${apiBase}/api/stats?user_id=${user.value.id}`, {
            credentials: 'include'
        });

        return response?.total_candidates || 0;
    };

    /**
     * 删除候选人
     */
    const deleteCandidate = async (id: number): Promise<boolean> => {
        if (!user.value) return false;

        try {
            await $fetch(`${apiBase}/api/candidates/${id}?user_id=${user.value.id}`, {
                method: 'DELETE',
                credentials: 'include'
            });
            return true;
        } catch (error) {
            console.error('Delete candidate failed:', error);
            return false;
        }
    };

    /**
     * 上传简历
     */
    const uploadResume = async (file: File): Promise<{ success: boolean; message?: string; candidate?: Candidate }> => {
        if (!user.value) {
            return { success: false, message: '请先登录' };
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('user_id', String(user.value.id));
        formData.append('source', 'upload');

        try {
            const response = await $fetch<any>(`${apiBase}/api/ingest`, {
                method: 'POST',
                body: formData,
                credentials: 'include'
            });

            return {
                success: true,
                candidate: response.candidate
            };
        } catch (error: any) {
            return {
                success: false,
                message: error?.data?.detail || '上传失败'
            };
        }
    };

    /**
     * 搜索候选人
     */
    const searchCandidates = async (query: string, topK: number = 20): Promise<Candidate[]> => {
        if (!user.value || !query) return [];

        const response = await $fetch<any>(`${apiBase}/api/search?q=${encodeURIComponent(query)}&user_id=${user.value.id}&top_k=${topK}`, {
            credentials: 'include'
        });

        return response?.candidates || [];
    };

    return {
        getCandidates,
        getCandidateCount,
        deleteCandidate,
        uploadResume,
        searchCandidates
    };
};
